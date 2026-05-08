import { json } from "../../transport/router.mjs";
import { boundedText } from "../../lib/validators.mjs";
import { normalizeRule, normalizeRuleManaged } from "../../lib/segmentRules.mjs";

export function createSegmentController({ db, jobs }) {
  return {
    async saveSegment(ctx, res) {
      const name = boundedText(ctx.body.name, 48);
      const rule = normalizeRule(ctx.body.rule);
      const result = await db.saveSegment(ctx.session.userId, name, { rule });
      return json(res, 201, result);
    },

    async saveSegmentManaged(ctx, res) {
      const name = boundedText(ctx.body.name, 48);
      const rule = normalizeRuleManaged(ctx.body.rule);
      const result = await db.saveSegment(ctx.session.userId, name, { rule });
      return json(res, 201, result);
    },

    async runSegment(ctx, res) {
      const output = await jobs.dispatch("segments.scan", {
        owner: ctx.session.userId,
        name: boundedText(ctx.query.name, 48),
        sample: boundedText(ctx.query.sample, 600)
      });
      return json(res, 200, output);
    },

    async runSegmentManaged(ctx, res) {
      const output = await jobs.dispatch("segments.scan.managed", {
        owner: ctx.session.userId,
        name: boundedText(ctx.query.name, 48),
        sample: boundedText(ctx.query.sample, 600)
      });
      return json(res, 200, output);
    }
  };
}
