import { json } from "../../transport/router.mjs";
import { requireTenant } from "../../lib/policy.mjs";
import { boundedText, tenantId } from "../../lib/validators.mjs";

export function createBillingController({ db }) {
  return {
    async invoice(ctx, res) {
      const tenant = tenantId(ctx.query.tenant);
      const invoiceId = boundedText(ctx.query.invoice, 60);
      const invoice = await db.invoice(tenant, invoiceId);
      return json(res, 200, invoice);
    },

    async invoiceScoped(ctx, res) {
      const tenant = requireTenant(ctx.session, tenantId(ctx.query.tenant));
      const invoiceId = boundedText(ctx.query.invoice, 60);
      const invoice = await db.invoice(tenant, invoiceId);
      return json(res, 200, invoice);
    }
  };
}
