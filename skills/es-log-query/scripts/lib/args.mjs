export function parseArgs(argv) {
  const positional = [];
  const values = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith("--")) {
      positional.push(arg);
      continue;
    }
    const key = arg.slice(2);
    const next = argv[i + 1];
    if (next == null || next.startsWith("--")) {
      values[key] = true;
      continue;
    }
    i += 1;
    if (values[key] == null) {
      values[key] = next;
    } else if (Array.isArray(values[key])) {
      values[key].push(next);
    } else {
      values[key] = [values[key], next];
    }
  }
  return { command: positional[0], positional, values };
}

export function listValue(value) {
  if (value == null) return [];
  return Array.isArray(value) ? value : [value];
}
