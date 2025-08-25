import {
  LOG_LEVEL_LABELS,
  PrivacyCenterSettings,
} from "~/app/server-utils/PrivacyCenterSettings";
import type { ConsentMethod } from "~/types/api";
import type {
  ConsentFlagType,
  ConsentNonApplicableFlagMode,
} from "~/types/config";

/**
 * Default value for how long to cache the /fides.js bundle for, in seconds.
 * This can be overriden via the FIDES_PRIVACY_CENTER__FIDES_JS_MAX_AGE_SECONDS
 * environment variable.
 */
export const DEFAULT_FIDES_JS_MAX_AGE_SECONDS = 60 * 60;

const defaultMissingExperienceBehavior = (
  setting: string | undefined,
): PrivacyCenterSettings["MISSING_EXPERIENCE_BEHAVIOR"] => {
  if (setting === "throw") {
    return "throw";
  }

  return "empty_experience";
};

const defaultLogLevel = (setting: any): PrivacyCenterSettings["LOG_LEVEL"] => {
  if (LOG_LEVEL_LABELS.includes(setting)) {
    return setting;
  }

  return "info";
};

const loadEnvironmentVariables = () => {
  // Load environment variables
  const settings: PrivacyCenterSettings = {
    FIDES_API_URL:
      process.env.FIDES_PRIVACY_CENTER__FIDES_API_URL ||
      "http://localhost:8080/api/v1",
    SERVER_SIDE_FIDES_API_URL:
      process.env.FIDES_PRIVACY_CENTER__SERVER_SIDE_FIDES_API_URL || null,
    FIDES_API_TOKEN: process.env.FIDES_PRIVACY_CENTER__FIDES_API_TOKEN || null,
    CONFIG_JSON_URL:
      process.env.FIDES_PRIVACY_CENTER__CONFIG_JSON_URL ||
      "file:///app/config/config.json",
    CONFIG_CSS_URL:
      process.env.FIDES_PRIVACY_CENTER__CONFIG_CSS_URL ||
      "file:///app/config/config.css",
    SHOW_BRAND_LINK:
      process.env.FIDES_PRIVACY_CENTER__SHOW_BRAND_LINK === "true" || false,
    ROOT_PROPERTY_PATH:
      process.env.FIDES_PRIVACY_CENTER__ROOT_PROPERTY_PATH || null,
    USE_API_CONFIG: process.env.FIDES_PRIVACY_CENTER__USE_API_CONFIG === "true", // default: false
    FIDES_JS_MAX_AGE_SECONDS:
      Number(process.env.FIDES_PRIVACY_CENTER__FIDES_JS_MAX_AGE_SECONDS) ||
      DEFAULT_FIDES_JS_MAX_AGE_SECONDS,
    MISSING_EXPERIENCE_BEHAVIOR: defaultMissingExperienceBehavior(
      process.env.FIDES_PRIVACY_CENTER__MISSING_EXPERIENCE_BEHAVIOR,
    ),
    LOG_LEVEL: defaultLogLevel(process.env.FIDES_PRIVACY_CENTER__LOG_LEVEL),
    ENABLE_EXTERNAL_TASK_PORTAL:
      process.env.FIDES_PRIVACY_CENTER__ENABLE_EXTERNAL_TASK_PORTAL === "true",

    // Overlay options
    DEBUG: process.env.FIDES_PRIVACY_CENTER__DEBUG
      ? process.env.FIDES_PRIVACY_CENTER__DEBUG === "true"
      : false,
    IS_OVERLAY_ENABLED: process.env.FIDES_PRIVACY_CENTER__IS_OVERLAY_ENABLED
      ? process.env.FIDES_PRIVACY_CENTER__IS_OVERLAY_ENABLED === "true"
      : false,
    IS_PREFETCH_ENABLED: process.env.FIDES_PRIVACY_CENTER__IS_PREFETCH_ENABLED
      ? process.env.FIDES_PRIVACY_CENTER__IS_PREFETCH_ENABLED === "true"
      : false,
    IS_GEOLOCATION_ENABLED: process.env
      .FIDES_PRIVACY_CENTER__IS_GEOLOCATION_ENABLED
      ? process.env.FIDES_PRIVACY_CENTER__IS_GEOLOCATION_ENABLED === "true"
      : false,
    GEOLOCATION_API_URL:
      process.env.FIDES_PRIVACY_CENTER__GEOLOCATION_API_URL || "",
    OVERLAY_PARENT_ID:
      process.env.FIDES_PRIVACY_CENTER__OVERLAY_PARENT_ID || null,
    MODAL_LINK_ID: process.env.FIDES_PRIVACY_CENTER__MODAL_LINK_ID || null,
    PRIVACY_CENTER_URL:
      process.env.FIDES_PRIVACY_CENTER__PRIVACY_CENTER_URL ||
      "http://localhost:3000",
    FIDES_EMBED: process.env.FIDES_PRIVACY_CENTER__FIDES_EMBED
      ? process.env.FIDES_PRIVACY_CENTER__FIDES_EMBED === "true"
      : false,
    FIDES_DISABLE_SAVE_API: process.env
      .FIDES_PRIVACY_CENTER__FIDES_DISABLE_SAVE_API
      ? process.env.FIDES_PRIVACY_CENTER__FIDES_DISABLE_SAVE_API === "true"
      : false,
    FIDES_DISABLE_NOTICES_SERVED_API: process.env
      .FIDES_PRIVACY_CENTER__FIDES_DISABLE_NOTICES_SERVED_API
      ? process.env.FIDES_PRIVACY_CENTER__FIDES_DISABLE_NOTICES_SERVED_API ===
        "true"
      : false,
    FIDES_DISABLE_BANNER: process.env.FIDES_PRIVACY_CENTER__FIDES_DISABLE_BANNER
      ? process.env.FIDES_PRIVACY_CENTER__FIDES_DISABLE_BANNER === "true"
      : false,
    FIDES_TCF_GDPR_APPLIES: !(
      process.env.FIDES_PRIVACY_CENTER__FIDES_TCF_GDPR_APPLIES === "false"
    ),
    FIDES_STRING: process.env.FIDES_PRIVACY_CENTER__FIDES_STRING || null,
    IS_FORCED_TCF: process.env.FIDES_PRIVACY_CENTER__IS_FORCED_TCF
      ? process.env.FIDES_PRIVACY_CENTER__IS_FORCED_TCF === "true"
      : false,
    FIDES_JS_BASE_URL:
      process.env.FIDES_PRIVACY_CENTER__FIDES_JS_BASE_URL ||
      "http://localhost:3000",
    CUSTOM_OPTIONS_PATH:
      process.env.FIDES_PRIVACY_CENTER__CUSTOM_OPTIONS_PATH || null,
    PREVENT_DISMISSAL: process.env.FIDES_PRIVACY_CENTER__PREVENT_DISMISSAL
      ? process.env.FIDES_PRIVACY_CENTER__PREVENT_DISMISSAL === "true"
      : false,
    ALLOW_HTML_DESCRIPTION: process.env
      .FIDES_PRIVACY_CENTER__ALLOW_HTML_DESCRIPTION
      ? process.env.FIDES_PRIVACY_CENTER__ALLOW_HTML_DESCRIPTION === "true"
      : null,
    BASE_64_COOKIE: process.env.FIDES_PRIVACY_CENTER__BASE_64_COOKIE
      ? process.env.FIDES_PRIVACY_CENTER__BASE_64_COOKIE === "true"
      : false,
    FIDES_PRIMARY_COLOR: process.env.FIDES_PRIVACY_CENTER__FIDES_PRIMARY_COLOR
      ? process.env.FIDES_PRIVACY_CENTER__FIDES_PRIMARY_COLOR
      : null,
    FIDES_CLEAR_COOKIE: process.env.FIDES_PRIVACY_CENTER__FIDES_CLEAR_COOKIE
      ? process.env.FIDES_PRIVACY_CENTER__FIDES_CLEAR_COOKIE === "true"
      : false,
    FIDES_CONSENT_OVERRIDE:
      (process.env.FIDES_PRIVACY_CENTER__FIDES_KNOWN_PREFERENCE as
        | ConsentMethod.ACCEPT
        | ConsentMethod.REJECT) || null,
    FIDES_DISABLED_NOTICES:
      process.env.FIDES_PRIVACY_CENTER__FIDES_DISABLED_NOTICES || null,
    FIDES_CONSENT_NON_APPLICABLE_FLAG_MODE:
      (process.env
        .FIDES_PRIVACY_CENTER__FIDES_CONSENT_NON_APPLICABLE_FLAG_MODE as ConsentNonApplicableFlagMode) ||
      null,
    FIDES_CONSENT_FLAG_TYPE:
      (process.env
        .FIDES_PRIVACY_CENTER__FIDES_CONSENT_FLAG_TYPE as ConsentFlagType) ||
      null,
    FIDES_INITIALIZED_EVENT_MODE:
      (process.env.FIDES_PRIVACY_CENTER__FIDES_INITIALIZED_EVENT_MODE as
        | "multiple"
        | "once"
        | "disable") || "once",
    FIDES_UNSUPPORTED_REPEATED_SCRIPT_LOADING:
      (process.env
        .FIDES_PRIVACY_CENTER__FIDES_UNSUPPORTED_REPEATED_SCRIPT_LOADING as
        | "enabled_acknowledge_not_supported"
        | "disabled") || "disabled",
  };
  return settings;
};
export default loadEnvironmentVariables;
