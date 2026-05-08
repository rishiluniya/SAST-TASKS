import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const manifest = JSON.parse(fs.readFileSync(path.join(root, "evaldata", "cases.json"), "utf8"));
const ids = new Set();

for (const item of manifest) {
  if (ids.has(item.id)) throw new Error(`duplicate manifest id ${item.id}`);
  ids.add(item.id);

  const filePath = path.join(root, item.sink.file);
  if (!fs.existsSync(filePath)) throw new Error(`missing file for ${item.id}: ${item.sink.file}`);
  const lines = fs.readFileSync(filePath, "utf8").split(/\r?\n/);
  if (item.sink.lineStart < 1 || item.sink.lineEnd > lines.length) {
    throw new Error(`line range outside file for ${item.id}`);
  }
}

await import(pathToFileURL(path.join(root, "apps", "node-ledger", "src", "server.mjs")));

console.log(
  JSON.stringify(
    {
      status: "ok",
      cases: manifest.length,
      primaryCases: manifest.filter((item) => item.variant === "case").length,
      controls: manifest.filter((item) => item.variant === "control").length
    },
    null,
    2
  )
);
