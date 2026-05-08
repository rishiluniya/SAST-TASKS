import { json } from "../../transport/router.mjs";
import { partnerWebhookUrl, weakWebhookCheck } from "../../lib/netGuard.mjs";

function later(fn) {
  return Promise.resolve().then(fn);
}

export function createIntegrationController({ db }) {
  return {
    async callWebhook(ctx, res) {
      const request = { ...ctx.body, url: String(ctx.body.url || "") };
      if (!weakWebhookCheck(request.url)) {
        return json(res, 400, { error: "bad_url" });
      }
      const audit = await db.query("select ? as webhook", [request.url]);
      const response = await later(() => fetch(request.url, { method: "POST", body: JSON.stringify(audit) }));
      return json(res, 200, { status: response.status });
    },

    async callPartnerWebhook(ctx, res) {
      const url = partnerWebhookUrl(ctx.body.url);
      const response = await later(() => fetch(url, { method: "POST", body: "{}" }));
      return json(res, 200, { status: response.status });
    }
  };
}
