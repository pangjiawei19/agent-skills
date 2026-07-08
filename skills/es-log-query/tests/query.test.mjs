import assert from "node:assert/strict";
import test from "node:test";
import { buildCountBody, buildSearchBody } from "../scripts/lib/query.mjs";

const fields = {
  time: "@timestamp",
  message: "message",
  level: "level",
};

test("buildSearchBody creates bool query from common filters", () => {
  const body = buildSearchBody({
    fields,
    start: "2026-07-08T00:00:00.000Z",
    end: "2026-07-08T01:00:00.000Z",
    message: "timeout",
    level: "error",
    terms: ["traceId=abc123"],
    matches: ["userAgent=Chrome"],
    size: 50,
    from: 10,
    sortOrder: "asc",
  });

  assert.equal(body.size, 50);
  assert.equal(body.from, 10);
  assert.deepEqual(body.sort, [{ "@timestamp": { order: "asc" } }]);
  assert.deepEqual(body.query.bool.must[0], {
    range: { "@timestamp": { format: "strict_date_optional_time", gte: "2026-07-08T00:00:00.000Z", lte: "2026-07-08T01:00:00.000Z" } },
  });
  assert.deepEqual(body.query.bool.must[1], { match: { message: "timeout" } });
  assert.deepEqual(body.query.bool.must[2], { match_phrase: { level: "error" } });
  assert.deepEqual(body.query.bool.must[3], { term: { traceId: "abc123" } });
  assert.deepEqual(body.query.bool.must[4], { match: { userAgent: "Chrome" } });
});

test("buildSearchBody accepts query string and source list", () => {
  const body = buildSearchBody({
    fields,
    queryString: 'level:error AND message:"timeout"',
    source: "message,level,@timestamp",
  });

  assert.deepEqual(body._source, ["message", "level", "@timestamp"]);
  assert.deepEqual(body.query.bool.must[0], {
    query_string: { query: 'level:error AND message:"timeout"' },
  });
});

test("buildSearchBody enforces size limit", () => {
  assert.throws(() => buildSearchBody({ fields, size: 1001 }), /size 最大值为 1000/);
});

test("buildCountBody omits pagination and sort", () => {
  const body = buildCountBody({ fields, level: "warn" });
  assert.deepEqual(body.query.bool.must[0], { match_phrase: { level: "warn" } });
  assert.equal(body.size, undefined);
  assert.equal(body.sort, undefined);
});
