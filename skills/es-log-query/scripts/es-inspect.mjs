#!/usr/bin/env node
import { parseArgs, listValue } from "./lib/args.mjs";
import { loadConfig, redactProfile, resolveFieldSet, resolveIndex, resolveProfile } from "./lib/config.mjs";
import { collectObservedFields, describeObservedFields, fieldCapsPatterns } from "./lib/discovery.mjs";
import { requestJson } from "./lib/http.mjs";
import { buildCountBody, buildDiscoverBody, buildTermsBody } from "./lib/query.mjs";
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
        hint: "检查配置、profile、index、字段列表、网络或权限。",
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

function commonQueryInput(values, fields) {
  return {
    fields,
    timeField: values["time-field"],
    start: values.start ? toIsoTime(values.start) : undefined,
    end: values.end ? toIsoTime(values.end) : undefined,
    message: values.message,
    level: values.level,
    terms: listValue(values.term),
    matches: listValue(values.match),
    queryString: values["query-string"],
  };
}

async function main(argv) {
  const { command, values } = parseArgs(argv);
  const config = await loadConfig({ configPath: values.config });
  if (command === "profiles") {
    const profiles = Object.fromEntries(Object.entries(config.profiles ?? {}).map(([name, profile]) => [name, redactProfile(profile)]));
    printOk({ defaultProfile: config.defaultProfile, profiles });
    return;
  }
  const { name: profileName, profile } = resolveProfile(config, values.profile);
  if (command === "indices") {
    printOk({ profile: profileName, indices: profile.indices ?? {} });
    return;
  }
  const index = resolveIndex(profile, values.index);
  if (command === "mapping") {
    const data = await requestJson({ profile, index, operation: "_mapping", method: "GET" });
    printOk({ profile: profileName, index, mapping: data });
    return;
  }
  if (command === "field-caps") {
    const query = values.fields ? { fields: values.fields } : undefined;
    const data = await requestJson({ profile, index, operation: "_field_caps", method: "GET", query });
    printOk({ profile: profileName, index, fieldCaps: data });
    return;
  }
  if (["count", "discover", "terms"].includes(command)) {
    const fields = resolveFieldSet(profile, values["field-set"] || "default");
    const queryInput = commonQueryInput(values, fields);
    if (command === "discover") {
      const body = buildDiscoverBody({ ...queryInput, sampleSize: values["sample-size"] });
      const data = await requestJson({ profile, index, operation: "_search", method: "POST", body });
      const hits = data.hits?.hits ?? [];
      const observed = collectObservedFields(hits, values["max-fields"]);
      const patterns = fieldCapsPatterns(observed.fields);
      const caps = patterns
        ? await requestJson({ profile, index, operation: "_field_caps", method: "GET", query: { fields: patterns } })
        : { fields: {} };
      const discovered = describeObservedFields(observed.fields, caps);
      printOk({
        profile: profileName,
        index,
        total: totalFromSearch(data),
        sampled: hits.length,
        totalObservedFields: observed.totalObservedFields,
        returnedFields: discovered.length,
        truncated: observed.truncated,
        fields: discovered,
      });
      return;
    }
    if (command === "terms") {
      const body = buildTermsBody({ ...queryInput, field: values.field, size: values.size });
      const data = await requestJson({ profile, index, operation: "_search", method: "POST", body });
      const aggregation = data.aggregations?.values ?? {};
      printOk({
        profile: profileName,
        index,
        field: values.field,
        total: totalFromSearch(data),
        returned: aggregation.buckets?.length ?? 0,
        sumOtherDocCount: aggregation.sum_other_doc_count ?? 0,
        buckets: (aggregation.buckets ?? []).map((bucket) => ({ key: bucket.key, count: bucket.doc_count })),
      });
      return;
    }
    const body = buildCountBody(queryInput);
    const data = await requestJson({ profile, index, operation: "_count", method: "POST", body });
    printOk({ profile: profileName, index, count: data.count ?? 0 });
    return;
  }
  throw new Error("用法：node scripts/es-inspect.mjs profiles|indices|mapping|field-caps|discover|terms|count");
}

main(process.argv.slice(2)).catch((err) => {
  printError(err);
  process.exitCode = 1;
});
