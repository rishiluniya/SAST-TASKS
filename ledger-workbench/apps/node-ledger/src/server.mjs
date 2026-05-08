import http from "node:http";
import { createRouter, json } from "./transport/router.mjs";
import { createLedgerDb } from "./data/db.mjs";
import { createReportController } from "./features/reports/reportController.mjs";
import { createExportController } from "./features/exports/exportController.mjs";
import { createIntegrationController } from "./features/integrations/integrationController.mjs";
import { createAdminController } from "./features/admin/adminController.mjs";
import { createBillingController } from "./features/billing/billingController.mjs";
import { createSettingsController } from "./features/settings/settingsController.mjs";
import { createSegmentController } from "./features/segments/segmentController.mjs";
import { createPortalController } from "./features/portal/portalController.mjs";
import { createMessageController } from "./features/messages/messageController.mjs";
import { createMatchingController } from "./features/matching/matchingController.mjs";
import { createJobRuntime } from "./runtime/jobs.mjs";

const db = createLedgerDb();
const reports = createReportController({ db });
const exportsController = createExportController({ db });
const integrations = createIntegrationController({ db });
const admin = createAdminController({ db });
const billing = createBillingController({ db });
const settings = createSettingsController({ db });
const jobs = createJobRuntime({ db });
const segments = createSegmentController({ db, jobs });
const portal = createPortalController({ db });
const messages = createMessageController({ db, jobs });
const matching = createMatchingController();

const router = createRouter();

router.get("/reports/search", reports.search);
router.get("/reports/search-managed", reports.searchManaged);
router.post("/reports/views", reports.saveView);
router.get("/reports/views/run", reports.runView);
router.get("/reports/views/run-preset", reports.runPresetView);
router.get("/reports/table", reports.tableHtml);
router.get("/reports/table-managed", reports.tableManagedHtml);
router.get("/exports/read", exportsController.readExport);
router.get("/exports/read-managed", exportsController.readManagedExport);
router.post("/integrations/webhook", integrations.callWebhook);
router.post("/integrations/webhook-managed", integrations.callPartnerWebhook);
router.get("/admin/diagnostics", admin.diagnostics);
router.get("/admin/diagnostics-managed", admin.diagnosticsManaged);
router.post("/admin/formula", admin.previewFormula);
router.post("/admin/formula-basic", admin.previewFormulaBasic);
router.post("/admin/token", admin.issueToken);
router.post("/admin/token-session", admin.issueSessionToken);
router.get("/billing/invoice", billing.invoice);
router.get("/billing/invoice-scoped", billing.invoiceScoped);
router.post("/settings/profile", settings.updateProfile);
router.post("/settings/profile-managed", settings.updateProfileManaged);
router.post("/segments", segments.saveSegment);
router.post("/segments-managed", segments.saveSegmentManaged);
router.get("/segments/run", segments.runSegment);
router.get("/segments/run-managed", segments.runSegmentManaged);
router.get("/portal/continue", portal.continueTo);
router.get("/portal/continue-managed", portal.continueManaged);
router.post("/messages/templates", messages.saveTemplate);
router.post("/messages/templates-managed", messages.saveTemplateManaged);
router.post("/messages/render", messages.renderTemplate);
router.post("/messages/render-managed", messages.renderTemplateManaged);
router.post("/matching/evaluate", matching.evaluate);

const server = http.createServer((req, res) => router.handle(req, res));

if (import.meta.url === `file://${process.argv[1]}`) {
  const port = Number(process.env.PORT || 0);
  server.listen(port, "127.0.0.1", () => {
    const address = server.address();
    console.log(`ledger-workbench listening on http://127.0.0.1:${address.port}`);
  });
}

export { server, json };
