import { json } from "../../transport/router.mjs";
import {
  compilePlanA,
  compilePlanB,
  compilePlanC,
  compilePlanD,
  compilePlanE,
  compilePlanF,
  compilePlanG,
  compilePlanH,
  compilePlanI,
  compilePlanJ,
  compilePlanK,
  compilePlanL,
  compilePlanM,
  compilePlanN,
  compilePlanO,
  compilePlanP,
  compilePlanQ,
  compilePlanR,
  compilePlanS,
  compilePlanT,
  compilePlanU,
  compilePlanV,
  compilePlanW,
  compilePlanX,
  compilePlanY,
  compilePlanZ,
  compilePlanAA,
  compilePlanAB,
  compilePlanAC,
  compilePlanAD,
  compilePlanAE,
  compilePlanAF,
  compilePlanAG,
  compilePlanAH,
  compilePlanAI,
  compilePlanAJ,
  compilePlanAK,
  compilePlanAL,
  compilePlanAM,
  compilePlanAN
} from "../../lib/matchPlans.mjs";

const registry = {
  one: [compilePlanA, compilePlanB],
  two: [compilePlanC, compilePlanD],
  three: [compilePlanE, compilePlanF],
  four: [compilePlanG, compilePlanH],
  five: [compilePlanI, compilePlanJ],
  six: [compilePlanK, compilePlanL],
  seven: [compilePlanM, compilePlanN],
  eight: [compilePlanO, compilePlanP],
  nine: [compilePlanQ, compilePlanR],
  ten: [compilePlanS, compilePlanT],
  eleven: [compilePlanU, compilePlanV],
  twelve: [compilePlanW, compilePlanX],
  thirteen: [compilePlanY, compilePlanZ],
  fourteen: [compilePlanAA, compilePlanAB],
  fifteen: [compilePlanAC, compilePlanAD],
  sixteen: [compilePlanAE, compilePlanAF],
  seventeen: [compilePlanAG, compilePlanAH],
  eighteen: [compilePlanAI, compilePlanAJ],
  nineteen: [compilePlanAK, compilePlanAL],
  twenty: [compilePlanAM, compilePlanAN]
};

export function createMatchingController() {
  return {
    async evaluate(ctx, res) {
      const pair = registry[ctx.body.group] || registry.one;
      const position = ctx.body.variant === "catalog" ? 1 : 0;
      const matcher = pair[position](ctx.body.record || {});
      const matched = matcher.test(String(ctx.body.sample || ""));
      return json(res, 200, { matched });
    }
  };
}
