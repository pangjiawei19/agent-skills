function parseKeyValue(value) {
  const text = String(value);
  const idx = text.indexOf("=");
  if (idx <= 0) throw new Error(`条件必须是 key=value：${text}`);
  return [text.slice(0, idx), text.slice(idx + 1)];
}

function addCommonFilters(must, input) {
  const fields = input.fields ?? {};
  const timeField = input.timeField || fields.time || "@timestamp";
  if (input.start || input.end) {
    const range = { format: "strict_date_optional_time" };
    if (input.start) range.gte = input.start;
    if (input.end) range.lte = input.end;
    must.push({ range: { [timeField]: range } });
  }
  if (input.message) must.push({ match: { [fields.message || "message"]: input.message } });
  if (input.level) must.push({ match_phrase: { [fields.level || "level"]: input.level } });
  if (input.queryString) must.push({ query_string: { query: input.queryString } });
  for (const item of input.terms ?? []) {
    const [key, value] = parseKeyValue(item);
    must.push({ term: { [key]: value } });
  }
  for (const item of input.matches ?? []) {
    const [key, value] = parseKeyValue(item);
    must.push({ match: { [key]: value } });
  }
}

function baseBody(input) {
  const must = [];
  addCommonFilters(must, input);
  return { query: must.length > 0 ? { bool: { must } } : { match_all: {} } };
}

export function buildSearchBody(input) {
  const size = Number(input.size ?? 100);
  if (!Number.isInteger(size) || size < 1) throw new Error("size 必须是正整数");
  if (size > 1000) throw new Error("size 最大值为 1000");
  const from = Number(input.from ?? 0);
  if (!Number.isInteger(from) || from < 0) throw new Error("from 必须是非负整数");
  const fields = input.fields ?? {};
  const timeField = input.timeField || fields.time || "@timestamp";
  const body = {
    ...baseBody(input),
    from,
    size,
    sort: [{ [timeField]: { order: input.sortOrder || "desc" } }],
  };
  if (input.source) {
    body._source = String(input.source)
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
  }
  return body;
}

export function buildCountBody(input) {
  return baseBody(input);
}
