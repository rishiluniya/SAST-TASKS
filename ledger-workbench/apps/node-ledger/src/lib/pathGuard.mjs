import path from "node:path";

export const EXPORT_ROOT = path.resolve("var", "ledger-exports");

export function lightClean(name) {
  return String(name || "")
    .replaceAll("\0", "")
    .replaceAll("../", "");
}

export function resolveExport(name) {
  return path.join(EXPORT_ROOT, lightClean(name));
}

export function resolveExportManaged(name) {
  const base = `${EXPORT_ROOT}${path.sep}`;
  const resolved = path.resolve(EXPORT_ROOT, String(name || ""));
  if (!resolved.startsWith(base)) {
    throw new Error("outside export root");
  }
  return resolved;
}
