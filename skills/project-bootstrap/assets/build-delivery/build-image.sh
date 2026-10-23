#!/usr/bin/env bash
# 在已配置 Docker/BuildKit、AWS CLI、Python 3 及团队 AWS 身份的 Runner 中执行。
set -euo pipefail
set +x

ci_build_stage=preflight
ci_image_status=failed
ci_docker_config=
ci_image_digest=
ci_command_pid=
ci_cancel_code=0
export CI_PUSH_STATE=not_attempted CI_IMAGE_ID= CI_IMAGE_URI= CI_IMAGE_TAG=

ci_cancel() {
  if ((ci_cancel_code == 0)); then ci_cancel_code=$1; fi
  if [[ -n "$ci_command_pid" ]]; then kill -TERM "$ci_command_pid" 2>/dev/null || :; fi
}

ci_run() {
  ((ci_cancel_code == 0)) || return "$ci_cancel_code"
  python3 scripts/ci/run-command.py --timeout "$ci_command_timeout" --grace "$ci_stop_seconds" "$@" &
  ci_command_pid=$!
  # 信号可能先于 PID 登记，登记后补发；等待被信号打断后仍等本次命令完成清理。
  if ((ci_cancel_code != 0)); then kill -TERM "$ci_command_pid" 2>/dev/null || :; fi
  local ci_command_code=0
  while :; do
    if wait "$ci_command_pid"; then ci_command_code=0; break; else ci_command_code=$?; fi
    kill -0 "$ci_command_pid" 2>/dev/null || break
  done
  ci_command_pid=
  if ((ci_cancel_code != 0)); then return "$ci_cancel_code"; fi
  return "$ci_command_code"
}

ci_finish() {
  local ci_exit_code=$?
  trap - EXIT
  trap '' INT TERM
  if ((ci_cancel_code != 0)); then ci_exit_code=$ci_cancel_code; fi
  if [[ -n "$ci_docker_config" ]]; then
    if ! rm -rf -- "$ci_docker_config"; then
      printf '%s\n' '无法清理本次 Docker 认证目录。' >&2
      if [[ "$ci_exit_code" == 0 ]]; then ci_exit_code=1; ci_build_stage=cleanup; fi
    fi
  fi
  if [[ "$ci_exit_code" != 0 ]]; then ci_image_status=failed; fi
  # 元信息失败不能覆盖原始构建错误；成功构建却无法保存结果则交付失败。
  if ! python3 scripts/ci/build-record.py --status "$ci_image_status" \
    --stage "$ci_build_stage" --exit-code "$ci_exit_code" --digest "$ci_image_digest"; then
    printf '%s\n' '无法保存镜像交付记录，请检查流水线。' >&2
    if [[ "$ci_exit_code" == 0 ]]; then ci_exit_code=1; fi
  fi
  exit "$ci_exit_code"
}
trap ci_finish EXIT
trap 'ci_cancel 130' INT
trap 'ci_cancel 143' TERM

for ci_required in AWS_REGION ECR_REGISTRY ECR_REPOSITORY IMAGE_COMPONENT IMAGE_TARGET \
  IMAGE_PLATFORM CI_JOB_ID CI_PIPELINE_ID CI_COMMIT_SHA CI_COMMIT_SHORT_SHA CI_IMAGE_SMOKE_COMMAND \
  CI_IMAGE_SCAN_COMMAND EXPECTED_IMAGE_SPECS; do
  if [[ -z "${!ci_required:-}" ]]; then
    printf '缺少 CI 参数：%s\n' "$ci_required" >&2
    exit 1
  fi
done
for ci_tool in docker aws python3; do command -v "$ci_tool" >/dev/null; done
[[ "${CI_PIPELINE_SOURCE:-}" == push && "${CI_COMMIT_REF_PROTECTED:-}" == true && \
   "${CI_COMMIT_BRANCH:-}" == release/* ]] || {
  printf '%s\n' '参考脚本只接受受保护 release 分支的 push 流水线。' >&2; exit 1;
}
[[ "$IMAGE_COMPONENT" =~ ^[a-z0-9][a-z0-9_.-]*$ ]] || { printf '%s\n' '组件名无效。' >&2; exit 1; }
[[ "$CI_JOB_ID" =~ ^[0-9]+$ && "$CI_PIPELINE_ID" =~ ^[0-9]+$ ]] || exit 1
[[ "$CI_COMMIT_SHA" =~ ^[a-f0-9]{40}([a-f0-9]{24})?$ ]] || exit 1
[[ "$CI_COMMIT_SHORT_SHA" =~ ^[a-f0-9]{7,16}$ ]] || exit 1
[[ "$CI_COMMIT_SHA" == "$CI_COMMIT_SHORT_SHA"* ]] || exit 1
[[ "$ECR_REGISTRY" =~ ^[0-9]{12}\.dkr\.ecr(-fips)?\.[a-z0-9-]+\.amazonaws\.com(\.cn)?$ ]] || {
  printf '%s\n' 'ECR_REGISTRY 必须是团队指定的私有 ECR 主机。' >&2; exit 1;
}
[[ "$ECR_REGISTRY" == *".${AWS_REGION}.amazonaws.com" || "$ECR_REGISTRY" == *".${AWS_REGION}.amazonaws.com.cn" ]] || exit 1
[[ "$ECR_REPOSITORY" =~ ^[a-z0-9][a-z0-9._/-]*$ ]] || exit 1
[[ "$IMAGE_PLATFORM" =~ ^linux/(amd64|arm64)(/v[0-9]+)?$ ]] || {
  printf '%s\n' '参考脚本仅支持单个 Linux 目标架构，多架构需适配 buildx。' >&2; exit 1;
}
ci_digest_attempts=${CI_ECR_DIGEST_ATTEMPTS-3}
[[ "$ci_digest_attempts" =~ ^[1-5]$ ]] || {
  printf '%s\n' 'CI_ECR_DIGEST_ATTEMPTS 必须为 1～5 的整数。' >&2; exit 1;
}
ci_command_timeout=${CI_COMMAND_TIMEOUT_SECONDS-900}
ci_stop_seconds=${CI_COMMAND_STOP_SECONDS-10}
[[ "$ci_command_timeout" =~ ^[1-9][0-9]{0,4}$ && "$ci_stop_seconds" =~ ^[1-9][0-9]?$ ]] &&
  ((ci_command_timeout <= 86400 && ci_stop_seconds <= 60)) || {
  printf '%s\n' '命令执行或停止预算无效。' >&2; exit 1;
}

export CI_IMAGE_TAG="release-${IMAGE_COMPONENT}-${CI_JOB_ID}-${CI_COMMIT_SHORT_SHA}"
export CI_IMAGE_URI="${ECR_REGISTRY}/${ECR_REPOSITORY}:${CI_IMAGE_TAG}"
python3 scripts/ci/build-record.py --preflight
ci_build_args=(build --file "${DOCKERFILE_PATH:-Dockerfile}" --target "$IMAGE_TARGET" \
  --platform "$IMAGE_PLATFORM" --tag "$CI_IMAGE_URI")
# 仅接受秘密的环境变量映射，不接受秘密值或任意 shell 参数。
# 示例：CI_BUILD_SECRETS=id=npm_token,env=NPM_AUTH_TOKEN；多项按行分隔。
while IFS= read -r ci_secret || [[ -n "$ci_secret" ]]; do
  [[ -z "$ci_secret" ]] && continue
  [[ "$ci_secret" =~ ^id=[a-zA-Z0-9_.-]+,env=[A-Z][A-Z0-9_]*$ ]] || {
    printf '%s\n' 'CI_BUILD_SECRETS 映射无效。' >&2; exit 1;
  }
  ci_secret_env=${ci_secret##*,env=}
  [[ -n "${!ci_secret_env:-}" ]] || { printf '缺少构建秘密变量：%s\n' "$ci_secret_env" >&2; exit 1; }
  ci_build_args+=(--secret "$ci_secret")
done <<< "${CI_BUILD_SECRETS:-}"

ci_docker_config=$(mktemp -d)
export DOCKER_CONFIG="$ci_docker_config"
export DOCKER_BUILDKIT=1
ci_build_stage=ecr_login
ci_run -- bash -euo pipefail -c 'aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"'

ci_build_stage=build
ci_run -- docker "${ci_build_args[@]}" "${BUILD_CONTEXT:-.}"

ci_build_stage=inspect
ci_run -- docker image inspect --format '{{.Id}}' "$CI_IMAGE_URI" > "$ci_docker_config/image-id"
IFS= read -r CI_IMAGE_ID < "$ci_docker_config/image-id"
[[ "$CI_IMAGE_ID" =~ ^sha256:[a-f0-9]{64}$ ]] || exit 1
export CI_IMAGE_ID

ci_build_stage=smoke
# 该命令由 Agent 根据目标工程落实，必须验证实际镜像行为并清理自己的资源。
ci_run -- bash -euo pipefail -c "$CI_IMAGE_SMOKE_COMMAND"

ci_build_stage=image_scan
# 工程适配器以 CI_IMAGE_ID 为扫描对象，保留报告并按安全模块判定，非零阻断推送。
ci_run --report-directory "security-reports/image/${IMAGE_COMPONENT}" -- bash -euo pipefail -c "$CI_IMAGE_SCAN_COMMAND"

ci_build_stage=verify_image
ci_run -- docker image inspect --format '{{.Id}}' "$CI_IMAGE_URI" > "$ci_docker_config/image-id-after"
IFS= read -r ci_image_after < "$ci_docker_config/image-id-after"
[[ "$ci_image_after" == "$CI_IMAGE_ID" ]] || exit 1

ci_build_stage=push
export CI_PUSH_STATE=unknown
ci_run -- docker push "$CI_IMAGE_URI"

ci_build_stage=resolve_digest
ci_digest_exit=1
for ((ci_attempt=1; ci_attempt<=ci_digest_attempts; ci_attempt++)); do
  if ci_run -- aws ecr describe-images --region "$AWS_REGION" \
    --registry-id "${ECR_REGISTRY%%.*}" --repository-name "$ECR_REPOSITORY" \
    --image-ids "imageTag=${CI_IMAGE_TAG}" --query 'imageDetails[0].imageDigest' --output text > "$ci_docker_config/digest" &&
    IFS= read -r ci_image_digest < "$ci_docker_config/digest" &&
    [[ "$ci_image_digest" =~ ^sha256:[a-f0-9]{64}$ ]]; then
    break
  else
    ci_digest_exit=$?
  fi
  ci_image_digest=
  ((ci_cancel_code == 0)) || exit "$ci_cancel_code"
  if ((ci_attempt < ci_digest_attempts)); then ci_run -- sleep 1; fi
done
[[ "$ci_image_digest" =~ ^sha256:[a-f0-9]{64}$ ]] || {
  printf '%s\n' '镜像已尝试推送，但未确认远端 digest，交付未完成。' >&2; exit "$ci_digest_exit";
}
export CI_PUSH_STATE=confirmed
((ci_cancel_code == 0)) || exit "$ci_cancel_code"
ci_build_stage=complete
ci_image_status=pushed
