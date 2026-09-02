import assert from "node:assert/strict";
import test from "node:test";
import {
  redactProfile,
  resolveIndex,
  resolveProfile,
} from "../scripts/lib/config.mjs";

const config = {
  defaultProfile: "prod",
  profiles: {
    prod: {
      node: "https://es.example.com:9200",
      auth: { username: "elastic", password: "secret" },
      indices: { app: "app-log-*" },
    },
  },
};

test("resolveProfile returns default profile when name is omitted", () => {
  const result = resolveProfile(config);
  assert.equal(result.name, "prod");
  assert.equal(result.profile.node, "https://es.example.com:9200");
});

test("resolveProfile throws for missing profile", () => {
  assert.throws(() => resolveProfile(config, "staging"), /未找到 profile/);
});

test("resolveIndex maps alias and accepts raw index pattern", () => {
  const { profile } = resolveProfile(config, "prod");
  assert.equal(resolveIndex(profile, "app"), "app-log-*");
  assert.equal(resolveIndex(profile, "raw-*"), "raw-*");
});

test("redactProfile removes password", () => {
  const safe = redactProfile(config.profiles.prod);
  assert.equal(safe.auth.password, "***");
});
