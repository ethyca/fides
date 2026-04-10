export const PLATFORM_LABELS: Record<string, string> = {
  google_workspace: "Google Workspace",
  gcp: "GCP",
};

export const formatPlatformLabel = (platform: string): string =>
  PLATFORM_LABELS[platform] ??
  platform.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

export const formatScopeKeyLabel = (key: string): string =>
  key.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());

export const DATA_CONSUMER_FORM_ID = "data-consumer-form";

/**
 * Pick the best display value from a scope object based on the consumer type.
 * Used in both the consumer form and the consumers table.
 */
export const getDisplayNameForScope = (
  scope: Record<string, string>,
  type?: string,
): string => {
  if (type === "google_group") {
    return scope.group_email ?? "";
  }
  if (type === "gcp_iam_role") {
    return scope.role ?? "";
  }
  if (type === "gcp_service_account") {
    return scope.email ?? "";
  }
  return (
    scope.group_email ??
    scope.role ??
    scope.email ??
    Object.values(scope).join(", ")
  );
};
