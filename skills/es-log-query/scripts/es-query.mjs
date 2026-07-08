#!/usr/bin/env node
import { readFile } from "node:fs/promises";
import { parseArgs, listValue } from "./lib/args.mjs";
import { loadConfig, resolveFieldSet, resolveIndex, resolveProfile } from "./lib/config.mjs";
import { requestJson } from "./lib/http.mjs";
import { buildSearchBody } from "./lib/query.mjs";
import { toIsoTime } from "./lib/time.mjs";

function printOk(data) {
  process.stdout.write(`${JSON.stringify({ ok: true, ...data }, null, 2)}\n`);
}

function printError(err) {
  process.stdout.write(
    `${JSON.stringify(
      {
        ok: false,
        error: { type: "error", message: err instanceof Error ? err.message : String(err) },
        hint: "检查 profile、index、时间范围、字段名、网络、认证或 ES DSL。",
      },
      null,
      2,
    )}\n`,
  );
}

function totalFromSearch(data) {
  const total = data.hits?.total;
  return typeof total === "number" ? total : total?.value ?? 0;
}

async function main(argv) {
  const { command, values } = parseArgs(argv);
  if (command !== "search") throw new Error("用法：node scripts/es-query.mjs search --index <index>");
  const config = await loadConfig({ configPath: values.config });
  const { name: profileName, profile } = resolveProfile(config, values.profile);
  const index = resolveIndex(profile, values.index);
  const fields = resolveFieldSet(profile, values["field-set"] || "default");
  let body;
  if (values.dsl) {
    body = JSON.parse(await readFile(values.dsl, "utf8"));
    if (body.size != null && Number(body.size) > 1000) throw new Error("size 最大值为 1000");
  } else {
    body = buildSearchBody({
      fields,
      timeField: values["time-field"],
      start: values.start ? toIsoTime(values.start) : undefined,
      end: values.end ? toIsoTime(values.end) : undefined,
      message: values.message,
      level: values.level,
      terms: listValue(values.term),
      matches: listValue(values.match),
      queryString: values["query-string"],
      size: values.size,
      from: values.from,
      sortOrder: values["sort-order"],
      source: values.source,
    });
  }
  const data = await requestJson({ profile, index, operation: "_search", method: "POST", body });
  const hits = data.hits?.hits ?? [];
  printOk({
    profile: profileName,
    index,
    total: totalFromSearch(data),
    returned: hits.length,
    logs: hits.map((hit) => ({ id: hit._id, ...(hit._source ?? {}) })),
    aggregations: data.aggregations ?? undefined,
  });
}

main(process.argv.slice(2)).catch((err) => {
  printError(err);
  process.exitCode = 1;
});
