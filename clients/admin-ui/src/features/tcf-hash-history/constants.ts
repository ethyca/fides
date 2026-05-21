import { CUSTOM_TAG_COLOR } from "fidesui";

type TagColor = `${CUSTOM_TAG_COLOR}`;

export enum TriggerSource {
  EXPERIENCE_CONFIG_UPDATE = "experience_config_update",
  EXPERIENCE_CONFIG_LIMITED_UPDATE = "experience_config_limited_update",
  EXPERIENCE_SERVE_UNCACHED = "experience_serve_uncached",
  COMPASS_SYNC = "compass_sync",
  TCF_CONFIGURATION_DELETE = "tcf_configuration_delete",
  TCF_PUBLISHER_RESTRICTION_CREATE = "tcf_publisher_restriction_create",
  TCF_PUBLISHER_RESTRICTION_UPDATE = "tcf_publisher_restriction_update",
  TCF_PUBLISHER_RESTRICTION_DELETE = "tcf_publisher_restriction_delete",
  UNKNOWN = "unknown",
}

export const TRIGGER_SOURCE_LABELS: Record<string, string> = {
  [TriggerSource.EXPERIENCE_CONFIG_UPDATE]: "Config update",
  [TriggerSource.EXPERIENCE_CONFIG_LIMITED_UPDATE]: "Limited update",
  [TriggerSource.EXPERIENCE_SERVE_UNCACHED]: "Served uncached",
  [TriggerSource.COMPASS_SYNC]: "Compass sync",
  [TriggerSource.TCF_CONFIGURATION_DELETE]: "Config deleted",
  [TriggerSource.TCF_PUBLISHER_RESTRICTION_CREATE]: "Restriction added",
  [TriggerSource.TCF_PUBLISHER_RESTRICTION_UPDATE]: "Restriction updated",
  [TriggerSource.TCF_PUBLISHER_RESTRICTION_DELETE]: "Restriction removed",
  [TriggerSource.UNKNOWN]: "Unknown",
};

export const TRIGGER_SOURCE_COLORS: Record<string, TagColor> = {
  [TriggerSource.EXPERIENCE_CONFIG_UPDATE]: "info",
  [TriggerSource.EXPERIENCE_CONFIG_LIMITED_UPDATE]: "default",
  [TriggerSource.EXPERIENCE_SERVE_UNCACHED]: "warning",
  [TriggerSource.COMPASS_SYNC]: "minos",
  [TriggerSource.TCF_CONFIGURATION_DELETE]: "error",
  [TriggerSource.TCF_PUBLISHER_RESTRICTION_CREATE]: "success",
  [TriggerSource.TCF_PUBLISHER_RESTRICTION_UPDATE]: "info",
  [TriggerSource.TCF_PUBLISHER_RESTRICTION_DELETE]: "error",
  [TriggerSource.UNKNOWN]: "default",
};

export const TRIGGER_SOURCE_DOT_COLORS: Record<string, string> = {
  [TriggerSource.EXPERIENCE_CONFIG_UPDATE]: "var(--fidesui-color-info)",
  [TriggerSource.EXPERIENCE_CONFIG_LIMITED_UPDATE]:
    "var(--fidesui-neutral-400)",
  [TriggerSource.EXPERIENCE_SERVE_UNCACHED]: "var(--fidesui-color-warning)",
  [TriggerSource.COMPASS_SYNC]: "var(--fidesui-brand-minos)",
  [TriggerSource.TCF_CONFIGURATION_DELETE]: "var(--fidesui-color-error)",
  [TriggerSource.TCF_PUBLISHER_RESTRICTION_CREATE]:
    "var(--fidesui-color-success)",
  [TriggerSource.TCF_PUBLISHER_RESTRICTION_UPDATE]: "var(--fidesui-color-info)",
  [TriggerSource.TCF_PUBLISHER_RESTRICTION_DELETE]:
    "var(--fidesui-color-error)",
  [TriggerSource.UNKNOWN]: "var(--fidesui-neutral-400)",
};
