import assert from "node:assert/strict";
import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";

async function writeConfig() {
  const dir = await mkdtemp(path.join(tmpdir(), "es-inspect-config-"));
  const configPath = path.join(dir, "config.json");
  await writeFile(
    configPath,
    JSON.stringify({
      defaultProfile: "prod",
      profiles: {
        prod: {
          node: "http://127.0.0.1:9",
          auth: { username: "elastic", password: "secret" },
          indices: { app: "app-log-*" },
          fieldSets: { default: { time: "@timestamp", message: "message", level: "level" } },
        },
      },
    }),
  );
  return configPath;
}

test("profiles command redacts password", async () => {
  const configPath = await writeConfig();
  const result = spawnSync(process.execPath, ["scripts/es-inspect.mjs", "profiles", "--config", configPath], {
    cwd: path.resolve("."),
    encoding: "utf8",
  });
  assert.equal(result.status, 0);
  const json = JSON.parse(result.stdout);
  assert.equal(json.ok, true);
  assert.equal(json.defaultProfile, "prod");
  assert.equal(json.profiles.prod.auth.password, "***");
});

test("indices command prints configured aliases", async () => {
  const configPath = await writeConfig();
  const result = spawnSync(process.execPath, ["scripts/es-inspect.mjs", "indices", "--config", configPath, "--profile", "prod"], {
    cwd: path.resolve("."),
    encoding: "utf8",
  });
  assert.equal(result.status, 0);
  const json = JSON.parse(result.stdout);
  assert.deepEqual(json.indices, { app: "app-log-*" });
});
