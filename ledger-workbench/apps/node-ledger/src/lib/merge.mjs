const blockedKeys = new Set(["__proto__", "prototype", "constructor"]);

export function mergeProfile(target, patch) {
  for (const [key, value] of Object.entries(patch || {})) {
    if (value && typeof value === "object" && !Array.isArray(value)) {
      target[key] = mergeProfile(target[key] || {}, value);
    } else {
      target[key] = value;
    }
  }
  return target;
}

export function mergeProfileManaged(target, patch) {
  for (const [key, value] of Object.entries(patch || {})) {
    if (blockedKeys.has(key)) continue;
    if (value && typeof value === "object" && !Array.isArray(value)) {
      target[key] = mergeProfileManaged(target[key] || {}, value);
    } else {
      target[key] = value;
    }
  }
  return target;
}
