function addLeafPaths(value, prefix, output) {
  if (Array.isArray(value)) {
    if (value.length === 0 && prefix) output.add(prefix);
    for (const item of value) addLeafPaths(item, prefix, output);
    return;
  }
  if (value && typeof value === "object") {
    const entries = Object.entries(value);
    if (entries.length === 0 && prefix) output.add(prefix);
    for (const [key, child] of entries) {
      addLeafPaths(child, prefix ? `${prefix}.${key}` : key, output);
    }
    return;
  }
  if (prefix) output.add(prefix);
}

function maxFieldsValue(value) {
  const maxFields = Number(value ?? 100);
  if (!Number.isInteger(maxFields) || maxFields < 1) throw new Error("max-fields 必须是正整数");
  if (maxFields > 200) throw new Error("max-fields 最大值为 200");
  return maxFields;
}

export function collectObservedFields(hits, maxFieldsInput) {
  const counts = new Map();
  for (const hit of hits ?? []) {
    const paths = new Set();
    addLeafPaths(hit?._source, "", paths);
    for (const field of paths) counts.set(field, (counts.get(field) ?? 0) + 1);
  }
  const all = [...counts.entries()]
    .map(([path, presentInSamples]) => ({ path, presentInSamples }))
    .sort((left, right) => right.presentInSamples - left.presentInSamples || left.path.localeCompare(right.path));
  const maxFields = maxFieldsValue(maxFieldsInput);
  return {
    fields: all.slice(0, maxFields),
    totalObservedFields: all.length,
    truncated: all.length > maxFields,
  };
}

export function fieldCapsPatterns(observedFields) {
  return observedFields.flatMap(({ path }) => [path, `${path}.*`]).join(",");
}

function sourcePathFor(field, observedFields) {
  return observedFields
    .filter(({ path }) => field === path || field.startsWith(`${path}.`))
    .sort((left, right) => right.path.length - left.path.length)[0]?.path;
}

export function describeObservedFields(observedFields, fieldCaps) {
  const counts = new Map(observedFields.map(({ path, presentInSamples }) => [path, presentInSamples]));
  const capFields = fieldCaps?.fields ?? {};
  const relatedCapFields = Object.keys(capFields).filter((path) => sourcePathFor(path, observedFields));
  const names = new Set([...counts.keys(), ...relatedCapFields]);
  return [...names].map((path) => {
    const sourcePath = sourcePathFor(path, observedFields) ?? path;
    const caps = Object.values(capFields[path] ?? {});
    const types = Object.keys(capFields[path] ?? {}).sort();
    return {
      path,
      sourcePath,
      types,
      searchable: caps.length > 0 && caps.every((cap) => cap.searchable === true),
      aggregatable: caps.length > 0 && caps.every((cap) => cap.aggregatable === true),
      typeConflict: types.length > 1,
      presentInSamples: counts.get(sourcePath) ?? 0,
    };
  }).sort((left, right) => right.presentInSamples - left.presentInSamples || left.path.localeCompare(right.path));
}
