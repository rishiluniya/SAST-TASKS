export function createLedgerDb() {
  const views = new Map();
  const segments = new Map();
  const templates = new Map();
  const rows = [
    {
      tenant_id: "tenant-alpha",
      report_id: "rpt-100",
      merchant: "Northwind",
      status: "settled",
      amount: 1250,
      note_html: "<strong>priority</strong>"
    },
    {
      tenant_id: "tenant-beta",
      report_id: "rpt-200",
      merchant: "Contoso",
      status: "review",
      amount: 77,
      note_html: "<img src=x onerror=alert(1)>"
    }
  ];

  return {
    async raw(sql) {
      return {
        sql,
        rows: rows.filter((row) => sql.includes(row.tenant_id))
      };
    },
    async query(sql, params = []) {
      const tenant = params[0] || "tenant-alpha";
      return {
        sql,
        params,
        rows: rows.filter((row) => row.tenant_id === tenant)
      };
    },
    async saveView(owner, name, fragment) {
      views.set(`${owner}:${name}`, { owner, name, fragment });
      return { owner, name };
    },
    async loadView(owner, name) {
      return views.get(`${owner}:${name}`) || null;
    },
    async saveSegment(owner, name, segment) {
      segments.set(`${owner}:${name}`, { owner, name, ...segment });
      return { owner, name };
    },
    async loadSegment(owner, name) {
      return segments.get(`${owner}:${name}`) || null;
    },
    async saveTemplate(owner, name, template) {
      templates.set(`${owner}:${name}`, { owner, name, ...template });
      return { owner, name };
    },
    async loadTemplate(owner, name) {
      return templates.get(`${owner}:${name}`) || null;
    },
    async recentReportRows(tenant) {
      return rows.filter((row) => row.tenant_id === tenant);
    },
    async invoice(tenant, invoiceId) {
      return {
        tenant,
        invoiceId,
        balance: tenant === "tenant-beta" ? 8000 : 42
      };
    }
  };
}
