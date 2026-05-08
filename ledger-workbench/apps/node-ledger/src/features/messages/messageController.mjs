import { json } from "../../transport/router.mjs";
import { boundedText } from "../../lib/validators.mjs";
import { normalizeTemplate } from "../../lib/messageTemplates.mjs";

export function createMessageController({ db, jobs }) {
  return {
    async saveTemplate(ctx, res) {
      const result = await db.saveTemplate(ctx.session.userId, boundedText(ctx.body.name, 48), {
        body: normalizeTemplate(ctx.body.body)
      });
      return json(res, 201, result);
    },

    async saveTemplateManaged(ctx, res) {
      const result = await db.saveTemplate(ctx.session.userId, boundedText(ctx.body.name, 48), {
        body: normalizeTemplate(ctx.body.body)
      });
      return json(res, 201, result);
    },

    async renderTemplate(ctx, res) {
      const output = await jobs.dispatch("messages.render", {
        owner: ctx.session.userId,
        name: boundedText(ctx.body.name, 48),
        data: ctx.body.data || {}
      });
      return json(res, 200, output);
    },

    async renderTemplateManaged(ctx, res) {
      const output = await jobs.dispatch("messages.render.managed", {
        owner: ctx.session.userId,
        name: boundedText(ctx.body.name, 48),
        data: ctx.body.data || {}
      });
      return json(res, 200, output);
    }
  };
}
