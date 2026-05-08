import { compilePattern, compilePatternManaged } from "../lib/segmentRules.mjs";

export function createSegmentJobs(runtime) {
  runtime.register("segments.scan", async ({ db, envelope }) => {
    const segment = await db.loadSegment(envelope.payload.owner, envelope.payload.name);
    const matcher = compilePattern(segment?.rule);
    return { matched: matcher(envelope.payload.sample || "") };
  });

  runtime.register("segments.scan.managed", async ({ db, envelope }) => {
    const segment = await db.loadSegment(envelope.payload.owner, envelope.payload.name);
    const matcher = compilePatternManaged(segment?.rule);
    return { matched: matcher(envelope.payload.sample || "") };
  });
}
