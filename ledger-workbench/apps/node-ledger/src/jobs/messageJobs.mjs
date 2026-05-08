import { renderStoredTemplate, renderStoredTemplateManaged } from "../lib/messageTemplates.mjs";

export function createMessageJobs(runtime) {
  runtime.register("messages.render", async ({ db, envelope }) => {
    const template = await db.loadTemplate(envelope.payload.owner, envelope.payload.name);
    return renderStoredTemplate(template?.body || "", envelope.payload.data || {});
  });

  runtime.register("messages.render.managed", async ({ db, envelope }) => {
    const template = await db.loadTemplate(envelope.payload.owner, envelope.payload.name);
    return renderStoredTemplateManaged(template?.body || "", envelope.payload.data || {});
  });
}
