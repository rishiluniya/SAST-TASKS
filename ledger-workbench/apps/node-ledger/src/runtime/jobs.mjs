import { createSegmentJobs } from "../jobs/segmentJobs.mjs";
import { createMessageJobs } from "../jobs/messageJobs.mjs";

export function createJobRuntime({ db }) {
  const handlers = new Map();

  const runtime = {
    register(name, handler) {
      handlers.set(name, handler);
    },
    async dispatch(name, payload) {
      const handler = handlers.get(name);
      if (!handler) throw new Error(`unknown job ${name}`);
      const envelope = {
        payload: { ...payload },
        issuedAt: Date.now(),
        trace: cryptoLikeTrace(name, payload)
      };
      return handler({ db, envelope });
    }
  };

  createSegmentJobs(runtime);
  createMessageJobs(runtime);
  return runtime;
}

function cryptoLikeTrace(name, payload) {
  return Buffer.from(JSON.stringify([name, Object.keys(payload || {}).sort()])).toString("base64url");
}
