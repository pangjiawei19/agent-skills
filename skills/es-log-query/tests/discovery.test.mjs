import assert from "node:assert/strict";
import test from "node:test";
import { collectObservedFields, describeObservedFields, fieldCapsPatterns } from "../scripts/lib/discovery.mjs";

test("discover collects nested field paths without sample values", () => {
  const hits = [
    { _source: { event: "started", status: 200, kubernetes: { labels: { app: "service-a" } } } },
    { _source: { event: "failed", error: { type: "timeout" }, kubernetes: { labels: { app: "service-a" } } } },
  ];
  const observed = collectObservedFields(hits, 20);
  assert.deepEqual(observed.fields.find((field) => field.path === "event"), { path: "event", presentInSamples: 2 });
  assert.deepEqual(observed.fields.find((field) => field.path === "error.type"), { path: "error.type", presentInSamples: 1 });
  assert.equal(JSON.stringify(observed).includes("service-a"), false);
  assert.match(fieldCapsPatterns(observed.fields), /event\.\*/);
});

test("discover combines observed fields with field capabilities", () => {
  const observed = [{ path: "event", presentInSamples: 2 }];
  const described = describeObservedFields(observed, {
    fields: {
      event: { text: { searchable: true, aggregatable: false } },
      "event.keyword": { keyword: { searchable: true, aggregatable: true } },
    },
  });
  assert.deepEqual(described, [
    {
      path: "event",
      sourcePath: "event",
      types: ["text"],
      searchable: true,
      aggregatable: false,
      typeConflict: false,
      presentInSamples: 2,
    },
    {
      path: "event.keyword",
      sourcePath: "event",
      types: ["keyword"],
      searchable: true,
      aggregatable: true,
      typeConflict: false,
      presentInSamples: 2,
    },
  ]);
});

test("discover enforces a compact field limit", () => {
  const observed = collectObservedFields([{ _source: { a: 1, b: 2, c: 3 } }], 2);
  assert.equal(observed.totalObservedFields, 3);
  assert.equal(observed.fields.length, 2);
  assert.equal(observed.truncated, true);
  assert.throws(() => collectObservedFields([], 201), /max-fields 最大值为 200/);
});
