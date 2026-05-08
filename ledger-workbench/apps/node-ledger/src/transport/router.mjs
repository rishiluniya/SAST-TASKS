import { parse } from "node:url";

export function json(res, status, body) {
  const payload = JSON.stringify(body);
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(payload)
  });
  res.end(payload);
}

export function html(res, status, body) {
  res.writeHead(status, {
    "content-type": "text/html; charset=utf-8",
    "content-length": Buffer.byteLength(body)
  });
  res.end(body);
}

export function createRouter() {
  const routes = new Map();

  function register(method, path, handler) {
    routes.set(`${method} ${path}`, handler);
  }

  return {
    get: (path, handler) => register("GET", path, handler),
    post: (path, handler) => register("POST", path, handler),
    async handle(req, res) {
      const parsed = parse(req.url, true);
      const handler = routes.get(`${req.method} ${parsed.pathname}`);
      if (!handler) return json(res, 404, { error: "not_found" });
      const context = await buildContext(req, parsed.query);
      try {
        return await handler(context, res);
      } catch (error) {
        return json(res, 500, { error: "internal", detail: String(error.message || error) });
      }
    }
  };
}

async function buildContext(req, query) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  const rawBody = Buffer.concat(chunks).toString("utf8");
  let body = {};
  if (rawBody) {
    try {
      body = JSON.parse(rawBody);
    } catch {
      body = { rawBody };
    }
  }
  return {
    req,
    query,
    body,
    headers: req.headers,
    session: decodeSession(req.headers.authorization)
  };
}

function decodeSession(header) {
  const fallback = {
    userId: "user-rishi",
    roles: ["analyst"],
    tenants: ["tenant-alpha"]
  };
  if (!header || !header.startsWith("Bearer ")) return fallback;
  try {
    return JSON.parse(Buffer.from(header.slice(7), "base64url").toString("utf8"));
  } catch {
    return fallback;
  }
}
