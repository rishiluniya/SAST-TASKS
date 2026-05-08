export function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export function table(rows, renderCell) {
  const body = rows
    .map((row) => `<tr>${Object.values(row).map(renderCell).join("")}</tr>`)
    .join("");
  return `<!doctype html><table>${body}</table>`;
}

export function rawCell(value) {
  return `<td>${value}</td>`;
}

export function escapedCell(value) {
  return `<td>${escapeHtml(value)}</td>`;
}
