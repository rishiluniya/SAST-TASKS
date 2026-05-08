import { chooseReturnTarget, chooseReturnTargetManaged } from "../../lib/redirects.mjs";

export function createPortalController() {
  return {
    async continueTo(ctx, res) {
      const location = chooseReturnTarget(ctx.query.next);
      res.writeHead(302, { location });
      res.end();
    },

    async continueManaged(ctx, res) {
      const location = chooseReturnTargetManaged(ctx.query.next);
      res.writeHead(302, { location });
      res.end();
    }
  };
}
