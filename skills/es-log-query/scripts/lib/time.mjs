const UNIT_MS = { s: 1000, m: 60_000, h: 3_600_000, d: 86_400_000 };

export function toIsoTime(value, nowMs = Date.now()) {
  const s = String(value ?? "").trim();
  const nowMatch = /^now([+-]\d+[smhd])?$/.exec(s);
  if (nowMatch) {
    if (!nowMatch[1]) return new Date(nowMs).toISOString();
    const sign = nowMatch[1][0] === "+" ? 1 : -1;
    const unit = nowMatch[1].slice(-1);
    const num = Number(nowMatch[1].slice(1, -1));
    return new Date(nowMs + sign * num * UNIT_MS[unit]).toISOString();
  }
  if (/^\d+$/.test(s)) {
    const num = Number(s);
    return new Date(s.length <= 10 ? num * 1000 : num).toISOString();
  }
  return s;
}
