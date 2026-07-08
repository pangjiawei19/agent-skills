import assert from "node:assert/strict";
import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";

test("es-query prints JSON error when config is missing", async () => {
  const dir = await mkdtemp(path.join(tmpdir(), "es-query-empty-"));
  const result = spawnSync(process.execPath, ["scripts/es-query.mjs", "search", "--config", path.join(dir, "missing.json"), "--index", "app"], {
    cwd: path.resolve("."),
    encoding: "utf8",
  });
  assert.notEqual(result.status, 0);
  const json = JSON.parse(result.stdout);
  assert.equal(json.ok, false);
  assert.equal(json.error.type, "error");
});

test("es-query rejects oversized size before network access", async () => {
  const dir = await mkdtemp(path.join(tmpdir(), "es-query-config-"));
  const configPath = path.join(dir, "config.json");
  await writeFile(
    configPath,
    JSON.stringify({
      defaultProfile: "prod",
      profiles: {
        prod: {
          node: "http://127.0.0.1:9",
          indices: { app: "app-log-*" },
          fieldSets: { default: { time: "@timestamp", message: "message", level: "level" } },
        },
      },
    }),
  );
  const result = spawnSync(process.execPath, ["scripts/es-query.mjs", "search", "--config", configPath, "--index", "app", "--size", "1001"], {
    cwd: path.resolve("."),
    encoding: "utf8",
  });
  assert.notEqual(result.status, 0);
  const json = JSON.parse(result.stdout);
  assert.match(json.error.message, /size 最大值为 1000/);
});
