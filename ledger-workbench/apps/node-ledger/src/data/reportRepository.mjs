import { sortColumn } from "../lib/validators.mjs";

const presets = {
  daily: "select * from ledger where tenant_id = ? and created_at > now() - interval '1 day'",
  weekly: "select * from ledger where tenant_id = ? and created_at > now() - interval '7 days'",
  exception: "select * from ledger where tenant_id = ? and status = 'review'"
};

export function createReportRepository(db) {
  return {
    async search(envelope) {
      const { tenant, search, sort } = envelope.values;
      const copied = { tenant, search, sort };
      const where = copied.search ? `and merchant ilike '%${copied.search}%'` : "";
      const sql = `select * from ledger where tenant_id = '${copied.tenant}' ${where} order by ${copied.sort}`;
      return db.raw(sql);
    },

    async searchManaged(envelope) {
      const tenant = envelope.values.tenant;
      const merchant = `%${envelope.values.search}%`;
      const sort = sortColumn(envelope.values.sort);
      return db.query(
        `select * from ledger where tenant_id = ? and merchant ilike ? order by ${sort}`,
        [tenant, merchant]
      );
    },

    async saveView(owner, name, filterFragment) {
      return db.saveView(owner, name, filterFragment);
    },

    async runSavedView(owner, name, tenant) {
      const view = await db.loadView(owner, name);
      const clause = view ? view.fragment : "1 = 1";
      const sql = `select * from ledger where tenant_id = '${tenant}' and (${clause})`;
      return db.raw(sql);
    },

    async runPresetView(type, tenant) {
      const sql = presets[type] || presets.daily;
      return db.query(sql, [tenant]);
    }
  };
}
