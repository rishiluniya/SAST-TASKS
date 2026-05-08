import { json } from "../../transport/router.mjs";
import { mergeProfile, mergeProfileManaged } from "../../lib/merge.mjs";

const profiles = new Map();

function profileFor(userId) {
  if (!profiles.has(userId)) {
    profiles.set(userId, {
      theme: "system",
      notifications: { email: true, sms: false }
    });
  }
  return profiles.get(userId);
}

export function createSettingsController() {
  return {
    async updateProfile(ctx, res) {
      const profile = profileFor(ctx.session.userId);
      const updated = mergeProfile(profile, ctx.body.patch);
      return json(res, 200, updated);
    },

    async updateProfileManaged(ctx, res) {
      const profile = profileFor(ctx.session.userId);
      const updated = mergeProfileManaged(profile, ctx.body.patch);
      return json(res, 200, updated);
    }
  };
}
