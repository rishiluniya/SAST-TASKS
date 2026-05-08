export function requireTenant(session, tenant) {
  if (!session.tenants.includes(tenant)) {
    throw new Error("tenant denied");
  }
  return tenant;
}

export function canUseAdminTool(session) {
  return session.roles.includes("admin") || session.roles.includes("support");
}

export function assertAdminTool(session) {
  if (!canUseAdminTool(session)) throw new Error("admin denied");
}
