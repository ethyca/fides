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
