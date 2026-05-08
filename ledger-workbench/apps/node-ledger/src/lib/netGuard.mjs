import net from "node:net";

const webhookHosts = new Set(["hooks.partner.test", "events.partner.test"]);

export function weakWebhookCheck(rawUrl) {
  const value = String(rawUrl || "");
  return value.startsWith("http") && !value.includes("localhost");
}

export function partnerWebhookUrl(rawUrl) {
  const url = new URL(String(rawUrl || ""));
  if (url.protocol !== "https:") throw new Error("https required");
  if (!webhookHosts.has(url.hostname)) throw new Error("host not approved");
  if (url.username || url.password) throw new Error("userinfo not allowed");
  if (net.isIP(url.hostname)) throw new Error("ip literal not allowed");
  return url;
}
