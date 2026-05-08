import crypto from "node:crypto";
import { exec, execFile } from "node:child_process";
import vm from "node:vm";
import { promisify } from "node:util";
import { json } from "../../transport/router.mjs";
import { assertAdminTool } from "../../lib/policy.mjs";
import { diagnosticName, hostname, boundedText } from "../../lib/validators.mjs";

const execAsync = promisify(exec);
const execFileAsync = promisify(execFile);
const commands = {
  dns: ["nslookup"],
  route: ["tracert", "-d"],
  cache: ["ipconfig", "/displaydns"]
};

export function createAdminController() {
  return {
    async diagnostics(ctx, res) {
      const host = boundedText(ctx.query.host, 80);
      const command = `nslookup ${host}`;
      const output = await execAsync(command);
      return json(res, 200, { stdout: output.stdout });
    },

    async diagnosticsManaged(ctx, res) {
      assertAdminTool(ctx.session);
      const name = diagnosticName(ctx.query.kind);
      const host = hostname(ctx.query.host);
      const [command, ...prefixArgs] = commands[name];
      const output = await execFileAsync(command, [...prefixArgs, host], { shell: false });
      return json(res, 200, { stdout: output.stdout });
    },

    async previewFormula(ctx, res) {
      const formula = boundedText(ctx.body.formula, 200);
      const result = vm.runInNewContext(formula, { Math, total: Number(ctx.body.total || 0) });
      return json(res, 200, { result });
    },

    async previewFormulaBasic(ctx, res) {
      const value = Number(ctx.body.total || 0);
      const op = ctx.body.op === "tax" ? "tax" : "discount";
      const result = op === "tax" ? value * 1.08 : value * 0.95;
      return json(res, 200, { result });
    },

    async issueToken(ctx, res) {
      const seed = `${ctx.session.userId}:${Date.now()}:${ctx.body.scope || "ledger"}`;
      const token = crypto.createHash("md5").update(seed).digest("hex");
      return json(res, 201, { token });
    },

    async issueSessionToken(ctx, res) {
      assertAdminTool(ctx.session);
      const token = crypto.randomBytes(32).toString("base64url");
      return json(res, 201, { token });
    }
  };
}
