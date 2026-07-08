import assert from "node:assert/strict";
import test from "node:test";
import { createEsUrl, requestJson } from "../scripts/lib/http.mjs";

test("createEsUrl builds only allowed paths", () => {
  assert.equal(createEsUrl("https://es.example.com", "app-log-*", "_search"), "https://es.example.com/app-log-*/_search");
  assert.throws(() => createEsUrl("https://es.example.com", "app-log-*", "_bulk"), /不允许的 ES 只读路径/);
});

test("createEsUrl supports read-only query parameters", () => {
  assert.equal(
    createEsUrl("https://es.example.com", "app-log-*", "_field_caps", { fields: "@timestamp,message" }),
    "https://es.example.com/app-log-*/_field_caps?fields=%40timestamp%2Cmessage",
  );
});

test("requestJson sends basic auth and parses JSON", async () => {
  const calls = [];
  const fetchImpl = async (url, options) => {
    calls.push({ url, options });
    return {
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ hits: { total: { value: 1 }, hits: [] } }),
    };
  };

  const result = await requestJson({
    fetchImpl,
    profile: {
      node: "https://es.example.com",
      auth: { username: "elastic", password: "secret" },
    },
    index: "app-log-*",
    operation: "_search",
    method: "POST",
    body: { query: { match_all: {} } },
  });

  assert.equal(result.hits.total.value, 1);
  assert.equal(calls[0].url, "https://es.example.com/app-log-*/_search");
  assert.equal(calls[0].options.headers.Authorization.startsWith("Basic "), true);
});

test("requestJson classifies HTTP errors", async () => {
  const fetchImpl = async () => ({
    ok: false,
    status: 401,
    text: async () => JSON.stringify({ error: { reason: "unauthorized" } }),
  });

  await assert.rejects(
    () =>
      requestJson({
        fetchImpl,
        profile: { node: "https://es.example.com" },
        index: "app-log-*",
        operation: "_search",
        method: "POST",
        body: {},
      }),
    /认证失败/,
  );
});
