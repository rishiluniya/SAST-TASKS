import { json, html } from "../../transport/router.mjs";
import { makeEnvelope, boundedText, tenantId, sortColumn, reportType } from "../../lib/validators.mjs";
import { requireTenant } from "../../lib/policy.mjs";
import { table, rawCell, escapedCell } from "../../lib/template.mjs";
import { createReportRepository } from "../../data/reportRepository.mjs";

export function createReportController({ db }) {
  const repo = createReportRepository(db);

  return {
    async search(ctx, res) {
      const envelope = makeEnvelope(ctx.query, {
        tenant: tenantId,
        search: boundedText,
        sort: boundedText
      });
      const result = await repo.search(envelope);
      return json(res, 200, result);
    },

    async searchManaged(ctx, res) {
      const envelope = makeEnvelope(ctx.query, {
        tenant: (value) => requireTenant(ctx.session, tenantId(value)),
        search: boundedText,
        sort: sortColumn
      });
      const result = await repo.searchManaged(envelope);
      return json(res, 200, result);
    },

    async saveView(ctx, res) {
      const name = boundedText(ctx.body.name, 40);
      const filter = boundedText(ctx.body.filter, 500);
      const result = await repo.saveView(ctx.session.userId, name, filter);
      return json(res, 201, result);
    },

    async runView(ctx, res) {
      const tenant = tenantId(ctx.query.tenant);
      const result = await repo.runSavedView(ctx.session.userId, boundedText(ctx.query.name, 40), tenant);
      return json(res, 200, result);
    },

    async runPresetView(ctx, res) {
      const tenant = requireTenant(ctx.session, tenantId(ctx.query.tenant));
      const result = await repo.runPresetView(reportType(ctx.query.type), tenant);
      return json(res, 200, result);
    },

    async tableHtml(ctx, res) {
      const rows = await db.recentReportRows(tenantId(ctx.query.tenant));
      return html(res, 200, table(rows, rawCell));
    },

    async tableManagedHtml(ctx, res) {
      const rows = await db.recentReportRows(requireTenant(ctx.session, tenantId(ctx.query.tenant)));
      return html(res, 200, table(rows, escapedCell));
    }
  };
}
