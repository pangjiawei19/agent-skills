#!/usr/bin/env node
import { parseArgs, listValue } from "./lib/args.mjs";
import { loadConfig, redactProfile, resolveFieldSet, resolveIndex, resolveProfile } from "./lib/config.mjs";
import { requestJson } from "./lib/http.mjs";
import { buildCountBody } from "./lib/query.mjs";
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
  if (command === "count") {
    const fields = resolveFieldSet(profile, values["field-set"] || "default");
    const body = buildCountBody({
      fields,
      timeField: values["time-field"],
      start: values.start ? toIsoTime(values.start) : undefined,
      end: values.end ? toIsoTime(values.end) : undefined,
      message: values.message,
      level: values.level,
      terms: listValue(values.term),
      matches: listValue(values.match),
      queryString: values["query-string"],
    });
    const data = await requestJson({ profile, index, operation: "_count", method: "POST", body });
    printOk({ profile: profileName, index, count: data.count ?? 0 });
    return;
  }
  throw new Error("用法：node scripts/es-inspect.mjs profiles|indices|mapping|field-caps|count");
}

main(process.argv.slice(2)).catch((err) => {
  printError(err);
  process.exitCode = 1;
});
