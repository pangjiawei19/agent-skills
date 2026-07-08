import assert from "node:assert/strict";
import test from "node:test";
import {
  redactProfile,
  resolveFieldSet,
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
      fieldSets: {
        default: { time: "@timestamp", message: "message", level: "level" },
        containerd: { time: "containerd_time", message: "message" },
      },
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

test("resolveFieldSet falls back to default", () => {
  const { profile } = resolveProfile(config, "prod");
  assert.equal(resolveFieldSet(profile).time, "@timestamp");
  assert.equal(resolveFieldSet(profile, "containerd").time, "containerd_time");
});

test("redactProfile removes password", () => {
  const safe = redactProfile(config.profiles.prod);
  assert.equal(safe.auth.password, "***");
});
