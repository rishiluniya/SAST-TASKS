const allowedOrigins = new Set(["https://ledger.example.test", "https://support.example.test"]);

export function chooseReturnTarget(value) {
  const target = String(value || "/");
  if (target.startsWith("/") || target.includes("ledger.example.test")) return target;
  return "/";
}

export function chooseReturnTargetManaged(value) {
  const url = new URL(String(value || "/"), "https://ledger.example.test");
  if (!allowedOrigins.has(url.origin)) return "/";
  return `${url.pathname}${url.search}${url.hash}`;
}
