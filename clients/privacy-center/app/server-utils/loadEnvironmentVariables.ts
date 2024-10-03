import { PrivacyCenterSettings } from "~/app/server-utils/PrivacyCenterSettings";

const loadEnvironmentVariables = () => {
  // Load environment variables
  const settings: PrivacyCenterSettings = {
    FIDES_API_URL:
      process.env.FIDES_PRIVACY_CENTER__FIDES_API_URL ||
      "http://localhost:8080/api/v1",
    SERVER_SIDE_FIDES_API_URL:
      process.env.FIDES_PRIVACY_CENTER__SERVER_SIDE_FIDES_API_URL || null,
    CONFIG_JSON_URL:
      process.env.FIDES_PRIVACY_CENTER__CONFIG_JSON_URL ||
      "file:///app/config/config.json",
    CONFIG_CSS_URL:
      process.env.FIDES_PRIVACY_CENTER__CONFIG_CSS_URL ||
      "file:///app/config/config.css",
    CUSTOM_PROPERTIES: process.env.CUSTOM_PROPERTIES === "true" || true,

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
    AUTOMATIC_SUBDOMAIN_COOKIE_DELETION: process.env
      .FIDES_PRIVACY_CENTER__AUTOMATIC_SUBDOMAIN_COOKIE_DELETION
      ? process.env
          .FIDES_PRIVACY_CENTER__AUTOMATIC_SUBDOMAIN_COOKIE_DELETION === "true"
      : false,
  };
  return settings;
};
export default loadEnvironmentVariables;
