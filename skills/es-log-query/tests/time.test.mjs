import assert from "node:assert/strict";
import test from "node:test";
import { toIsoTime } from "../scripts/lib/time.mjs";

const base = Date.parse("2026-07-08T00:00:00.000Z");

test("toIsoTime supports now and relative offsets", () => {
  assert.equal(toIsoTime("now", base), "2026-07-08T00:00:00.000Z");
  assert.equal(toIsoTime("now-30m", base), "2026-07-07T23:30:00.000Z");
  assert.equal(toIsoTime("now+2h", base), "2026-07-08T02:00:00.000Z");
});

test("toIsoTime supports second and millisecond timestamps", () => {
  assert.equal(toIsoTime("1767225600", base), "2026-01-01T00:00:00.000Z");
  assert.equal(toIsoTime("1767225600000", base), "2026-01-01T00:00:00.000Z");
});

test("toIsoTime returns ISO-like values unchanged", () => {
  assert.equal(toIsoTime("2026-07-08T12:00:00+08:00", base), "2026-07-08T12:00:00+08:00");
});
