const ALLOWED_OPERATIONS = new Set(["_search", "_count", "_mapping", "_field_caps"]);

function encodeIndex(index) {
  return String(index)
    .split("/")
    .map((part) => encodeURIComponent(part).replaceAll("%2A", "*").replaceAll("%2C", ","))
    .join("/");
}

export function createEsUrl(node, index, operation, query) {
  if (!ALLOWED_OPERATIONS.has(operation)) {
    throw new Error(`不允许的 ES 只读路径：${operation}`);
  }
  const base = String(node).replace(/\/+$/, "");
  const safeIndex = encodeIndex(index);
  const search = query ? `?${new URLSearchParams(query).toString()}` : "";
  return `${base}/${safeIndex}/${operation}${search}`;
}

function createHeaders(profile, hasBody) {
  const headers = {};
  if (hasBody) headers["Content-Type"] = "application/json";
  if (profile.auth?.username && profile.auth?.password) {
    const token = Buffer.from(`${profile.auth.username}:${profile.auth.password}`).toString("base64");
    headers.Authorization = `Basic ${token}`;
  }
  return headers;
}

function classifyHttpError(status, text) {
  if (status === 401) return `认证失败：${text}`;
  if (status === 403) return `权限不足：${text}`;
  if (status === 404) return `索引或路径不存在：${text}`;
  return `Elasticsearch HTTP ${status}：${text}`;
}

export async function requestJson(input) {
  const fetchImpl = input.fetchImpl ?? globalThis.fetch;
  if (typeof fetchImpl !== "function") throw new Error("当前 Node.js 运行时没有 fetch");
  const url = createEsUrl(input.profile.node, input.index, input.operation, input.query);
  const controller = new AbortController();
  const timeout = input.profile.requestTimeoutMs ?? 30_000;
  const timer = setTimeout(() => controller.abort(), timeout);
  const previousTls = process.env.NODE_TLS_REJECT_UNAUTHORIZED;
  if (input.profile.insecure && url.startsWith("https://")) {
    process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";
  }
  const options = {
    method: input.method,
    headers: createHeaders(input.profile, input.body != null),
    signal: controller.signal,
  };
  if (input.body != null) options.body = JSON.stringify(input.body);
  try {
    const res = await fetchImpl(url, options);
    const text = await res.text();
    if (!res.ok) throw new Error(classifyHttpError(res.status, text.slice(0, 500)));
    if (!text) return {};
    try {
      return JSON.parse(text);
    } catch {
      throw new Error(`Elasticsearch 响应不是 JSON：${text.slice(0, 300)}`);
    }
  } catch (err) {
    if (err.name === "AbortError") throw new Error(`Elasticsearch 请求超时：${timeout}ms`);
    throw err;
  } finally {
    clearTimeout(timer);
    if (previousTls == null) {
      delete process.env.NODE_TLS_REJECT_UNAUTHORIZED;
    } else {
      process.env.NODE_TLS_REJECT_UNAUTHORIZED = previousTls;
    }
  }
}
