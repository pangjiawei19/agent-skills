import { readFile } from "node:fs/promises";
import { homedir } from "node:os";
import path from "node:path";

export const DEFAULT_CONFIG_PATH = path.join(homedir(), ".config", "es-log-query", "config.json");

export async function loadConfig(options = {}) {
  const configPath = options.configPath ?? DEFAULT_CONFIG_PATH;
  let raw;
  try {
    raw = await readFile(configPath, "utf8");
  } catch (err) {
    throw new Error(`读取配置失败：${configPath}。${err.message}`);
  }
  try {
    return JSON.parse(raw);
  } catch (err) {
    throw new Error(`配置不是合法 JSON：${configPath}。${err.message}`);
  }
}

export function resolveProfile(config, profileName) {
  const name = profileName || config.defaultProfile;
  if (!name) throw new Error("未指定 profile，且配置中没有 defaultProfile");
  const profile = config.profiles?.[name];
  if (!profile) throw new Error(`未找到 profile：${name}`);
  if (!profile.node) throw new Error(`profile 缺少 node：${name}`);
  return { name, profile };
}

export function resolveIndex(profile, indexName) {
  if (!indexName) throw new Error("缺少 --index");
  return profile.indices?.[indexName] ?? indexName;
}

export function resolveFieldSet(profile, fieldSetName = "default") {
  const fields = profile.fieldSets?.[fieldSetName] ?? profile.fieldSets?.default;
  if (!fields) throw new Error(`未找到 field set：${fieldSetName}`);
  return fields;
}

export function redactProfile(profile) {
  return {
    ...profile,
    auth: profile.auth
      ? {
          ...profile.auth,
          password: profile.auth.password ? "***" : undefined,
        }
      : undefined,
  };
}
