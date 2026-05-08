export function normalizeRule(input) {
  const rule = input && typeof input === "object" ? input : {};
  return {
    pattern: String(rule.pattern || "").slice(0, 240),
    flags: String(rule.flags || "").replace(/[^gimsuy]/g, "").slice(0, 6)
  };
}

export function normalizeRuleManaged(input) {
  const rule = normalizeRule(input);
  return {
    pattern: escapeRegex(rule.pattern).slice(0, 120),
    flags: rule.flags.replace(/[gy]/g, "")
  };
}

export function compilePattern(rule) {
  const current = normalizeRule(rule);
  const compiled = new RegExp(current.pattern, current.flags);
  return (sample) => compiled.test(String(sample || ""));
}

export function compilePatternManaged(rule) {
  const current = normalizeRuleManaged(rule);
  const compiled = new RegExp(current.pattern, current.flags);
  return (sample) => compiled.test(String(sample || ""));
}

function escapeRegex(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
