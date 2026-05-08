const sortColumns = new Set(["created_at", "amount", "merchant", "status"]);
const reportTypes = new Set(["daily", "weekly", "exception"]);
const diagnostics = new Set(["dns", "route", "cache"]);

export function text(value, fallback = "") {
  return typeof value === "string" ? value : fallback;
}

export function boundedText(value, max = 120) {
  return text(value).slice(0, max);
}

export function enumValue(value, allowed, fallback) {
  return allowed.has(value) ? value : fallback;
}

export function sortColumn(value) {
  return enumValue(value, sortColumns, "created_at");
}

export function reportType(value) {
  return enumValue(value, reportTypes, "daily");
}

export function diagnosticName(value) {
  return enumValue(value, diagnostics, "dns");
}

export function tenantId(value) {
  const candidate = text(value);
  if (/^tenant-[a-z0-9-]{1,32}$/.test(candidate)) return candidate;
  return "tenant-alpha";
}

export function hostname(value) {
  const candidate = text(value);
  if (/^[a-z0-9.-]{1,80}$/i.test(candidate)) return candidate;
  return "localhost";
}

export function positiveInt(value, fallback = 25) {
  const number = Number(value);
  return Number.isInteger(number) && number > 0 && number < 500 ? number : fallback;
}

export function makeEnvelope(source, fields) {
  const normalized = {};
  for (const [key, normalizer] of Object.entries(fields)) {
    normalized[key] = normalizer(source[key]);
  }
  return Object.freeze({
    meta: { normalizedAt: Date.now() },
    values: Object.freeze(normalized)
  });
}

export function shallowClone(value) {
  return { ...value };
}
