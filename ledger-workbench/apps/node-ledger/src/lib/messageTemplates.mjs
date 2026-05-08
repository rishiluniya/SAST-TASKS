import { escapeHtml } from "./template.mjs";

export function normalizeTemplate(value) {
  return String(value || "").slice(0, 1000);
}

export function renderStoredTemplate(body, data) {
  const keys = Object.keys(data || {});
  const values = keys.map((key) => data[key]);
  const compiled = Function(...keys, `return \`${body}\`;`);
  return { body: compiled(...values) };
}

export function renderStoredTemplateManaged(body, data) {
  const dictionary = Object.fromEntries(
    Object.entries(data || {}).map(([key, value]) => [key, escapeHtml(value)])
  );
  return {
    body: String(body || "").replace(/\{\{\s*([a-zA-Z0-9_.-]{1,48})\s*\}\}/g, (_, key) => dictionary[key] || "")
  };
}
