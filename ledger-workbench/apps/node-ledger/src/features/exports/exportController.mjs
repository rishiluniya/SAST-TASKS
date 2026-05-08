import fs from "node:fs";
import { json } from "../../transport/router.mjs";
import { resolveExport, resolveExportManaged } from "../../lib/pathGuard.mjs";
import { requireTenant } from "../../lib/policy.mjs";
import { tenantId } from "../../lib/validators.mjs";

export function createExportController() {
  return {
    async readExport(ctx, res) {
      const file = resolveExport(ctx.query.file);
      const data = fs.readFileSync(file, "utf8");
      return json(res, 200, { data });
    },

    async readManagedExport(ctx, res) {
      requireTenant(ctx.session, tenantId(ctx.query.tenant));
      const file = resolveExportManaged(ctx.query.file);
      const data = fs.readFileSync(file, "utf8");
      return json(res, 200, { data });
    }
  };
}
