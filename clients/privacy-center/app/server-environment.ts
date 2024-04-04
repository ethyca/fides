/* eslint-disable no-console,consistent-return */
/**
 * Utility functions and logic that is designed to exclusively run server-side to configure the environment for the app, e.g.:
 * 1) Securely loading ENV variables for the client to use
 * 2) Fetching configuration files (config.json, config.css) to inject into the client
 * 3) etc.
 *
 * During server-side rendering, call loadPrivacyCenterEnvironment() to initialize the environment values for the App.
 */
import { URL } from "url";

import {
  isV1ConsentConfig,
  translateV1ConfigToV2,
} from "~/features/consent/helpers";
import {
  LegacyConfig,
  LegacyConsentConfig,
  Config,
  ConsentConfig,
} from "~/types/config";

/**
 * SERVER-SIDE functions
 */

/**
 * Settings that can be controlled using ENV vars on the server.
 *
 * Any of these can be set by adding the prefix "FIDES_PRIVACY_CENTER__", e.g.
 *
 * FIDES_PRIVACY_CENTER__FIDES_API_URL=https://fides.example.com/api/v1
 */
export interface PrivacyCenterSettings {
  // Privacy center settings
  FIDES_API_URL: string; // e.g. http://localhost:8080/api/v1
  SERVER_SIDE_FIDES_API_URL: string | null; // e.g. http://fides:8080/api/v1
  CONFIG_CSS_URL: string; // e.g. file:///app/config/config.css
  CONFIG_JSON_URL: string; // e.g. file:///app/config/config.json

  // Fides.js options
  DEBUG: boolean; // whether console logs are enabled for consent components
  GEOLOCATION_API_URL: string; // e.g. http://location-cdn.com
  IS_GEOLOCATION_ENABLED: boolean; // whether we should use geolocation to drive privacy experience
  IS_OVERLAY_ENABLED: boolean; // whether we should render privacy-experience-driven components
  IS_PREFETCH_ENABLED: boolean | false; // (optional) whether we should pre-fetch geolocation and experience server-side
  OVERLAY_PARENT_ID: string | null; // (optional) ID of the parent DOM element where the overlay should be inserted
  MODAL_LINK_ID: string | null; // (optional) ID of the DOM element that should trigger the consent modal
  PRIVACY_CENTER_URL: string; // e.g. http://localhost:3000
  FIDES_EMBED: boolean | false; // (optional) Whether we should "embed" the fides.js overlay UI (ie. “Layer 2”) into a web page
  FIDES_DISABLE_SAVE_API: boolean | false; // (optional) Whether we should disable saving consent preferences to the Fides API
  FIDES_DISABLE_BANNER: boolean | false; // (optional) Whether we should disable showing the banner
  FIDES_TCF_GDPR_APPLIES: boolean; // (optional) The default for the TCF GDPR applies value (default true)
  FIDES_STRING: string | null; // (optional) An explicitly passed-in string that supersedes the cookie. Can contain both TC and AC strings
  IS_FORCED_TCF: boolean; // whether to force the privacy center to use the fides-tcf.js bundle
  FIDES_JS_BASE_URL: string; // A base URL to a directory of fides.js scripts
  CUSTOM_OPTIONS_PATH: string | null; // (optional) A custom path to fetch FidesOptions (e.g. "window.config.overrides"). Defaults to window.fides_overrides
  PREVENT_DISMISSAL: boolean; // whether or not the user is allowed to dismiss the banner/overlay
  ALLOW_HTML_DESCRIPTION: boolean | null; // (optional) whether or not HTML descriptions should be rendered
  BASE_64_COOKIE: boolean; // whether or not to encode cookie as base64 on top of the default JSON string
  FIDES_PRIMARY_COLOR: string | null; // (optional) sets fides primary color
}

/**
 * Subset of PrivacyCenterSettings that are forwarded to the client.
 *
 * NOTE: Since these are exposed on the client, they cannot contain any secrets!
 */
export type PrivacyCenterClientSettings = Pick<
  PrivacyCenterSettings,
  | "FIDES_API_URL"
  | "SERVER_SIDE_FIDES_API_URL"
  | "DEBUG"
  | "GEOLOCATION_API_URL"
  | "IS_GEOLOCATION_ENABLED"
  | "IS_OVERLAY_ENABLED"
  | "IS_PREFETCH_ENABLED"
  | "OVERLAY_PARENT_ID"
  | "MODAL_LINK_ID"
  | "PRIVACY_CENTER_URL"
  | "FIDES_EMBED"
  | "FIDES_DISABLE_SAVE_API"
  | "FIDES_DISABLE_BANNER"
  | "FIDES_TCF_GDPR_APPLIES"
  | "FIDES_STRING"
  | "IS_FORCED_TCF"
  | "FIDES_JS_BASE_URL"
  | "CUSTOM_OPTIONS_PATH"
  | "PREVENT_DISMISSAL"
  | "ALLOW_HTML_DESCRIPTION"
  | "BASE_64_COOKIE"
  | "FIDES_PRIMARY_COLOR"
>;

export type Styles = string;

/**
 * Environment that is generated server-side and provided to the client
 */
export interface PrivacyCenterEnvironment {
  settings: PrivacyCenterClientSettings;
  config?: Config;
  styles?: Styles;
}

/**
 * Load a config file from the given list of URLs, trying them in order until one is successfully read.
 */
const loadConfigFile = async (
  urls: (string | undefined)[]
): Promise<string | undefined> => {
  // Dynamically import the "fs" module to read from the filesystem. This module
  // doesn't exist in the browser context, so to allow the bundler to function
  // we provide a (non-functional) fallback for "fs" in the webpack config (see
  // next.config.js)
  const fsPromises = (await import("fs")).promises;
  if (!fsPromises) {
    throw new Error("Unable to load 'fs' module!");
  }

  // Loop through the provided URLs, testing each one in order, and return the
  // first file that loads.
  /* eslint-disable no-restricted-syntax,no-continue,no-await-in-loop */
  for (const urlString of urls) {
    try {
      if (!urlString) {
        continue;
      }
      const url: URL = new URL(urlString);
      // DEFER: add support for https:// to fetch remote config files!
      if (url.protocol !== "file:") {
        throw new Error(
          `Config file URLs currently must use the 'file:' protocol: ${urlString}`
        );
      }
      // Relative paths (e.g. "file:./") aren't supported by node's URL class.
      // So to support this, we just use a path string instead!
      let path;
      if (urlString.startsWith("file:.")) {
        path = urlString.replace("file:", "");
      }
      const file = await fsPromises.readFile(path || url, "utf-8");
      if (process.env.NODE_ENV === "development") {
        console.log(`Loaded configuration file: ${urlString}`);
      }
      return file;
    } catch (err: any) {
      // Catch "file not found" errors (ENOENT)
      if (err.code === "ENOENT") {
        continue;
      }
      // Log everything else and continue
      console.log(
        `Failed to load configuration file from ${urlString}. Error: `,
        err
      );
    }
  }
  /* eslint-enable no-restricted-syntax,no-continue,no-await-in-loop */
};

/**
 * Transform the config to the latest version so that components can
 * reference config variables uniformly.
 */
export const transformConfig = (config: LegacyConfig): Config => {
  if (isV1ConsentConfig(config.consent)) {
    const v1ConsentConfig: LegacyConsentConfig = config.consent;
    const translatedConsent: ConsentConfig = translateV1ConfigToV2({
      v1ConsentConfig,
    });
    return { ...config, consent: translatedConsent };
  }
  return { ...config, consent: config.consent };
};

/**
 * Validate the config object
 */
export const validateConfig = (
  input: Config | LegacyConfig
): { isValid: boolean; message: string } => {
  // First, ensure we support LegacyConfig type if provided
  const config = transformConfig(input);

  // Cannot currently have more than one consent be executable
  if (config.consent) {
    const options = config.consent.page.consentOptions;
    const executables = options.filter((option) => option.executable);
    if (executables.length > 1) {
      return {
        isValid: false,
        message: "Cannot have more than one consent option be executable",
      };
    }
  }

  const invalidFieldMessages = config.actions.flatMap((action) => {
    const invalidFields = Object.entries(
      action.custom_privacy_request_fields || {}
    )
      .filter(([, field]) => field.hidden && field.default_value === undefined)
      .map(([key]) => `'${key}'`);

    return invalidFields.length > 0
      ? [
          `${invalidFields.join(", ")} in the action with policy_key '${
            action.policy_key
          }'`,
        ]
      : [];
  });

  if (invalidFieldMessages.length > 0) {
    return {
      isValid: false,
      message: `A default_value is required for hidden field(s) ${invalidFieldMessages.join(
        ", "
      )}`,
    };
  }

  return { isValid: true, message: "Config is valid" };
};

/**
 * Load the config.json file from the given URL, or fallback to default filesystem paths.
 *
 * Loading precedence is:
 * 1) Load from `configJsonUrl` argument
 * 2) Load from file:///app/config/config.json on filesystem (absolute path)
 * 3) Load from file:./config/config.json on filesystem (relative path)
 *
 * NOTE: The "/app/config" path is for backwards-compatibility with the initial
 * version of ethyca/fides-privacy-center, which expected to always load the
 * configuration file from this well-known path.
 */
export const loadConfigFromFile = async (
  configJsonUrl?: string
): Promise<Config | undefined> => {
  const urls = [
    configJsonUrl,
    "file:///app/config/config.json",
    "file:./config/config.json",
  ];
  const file = await loadConfigFile(urls);
  if (file) {
    const config = transformConfig(JSON.parse(file));
    const { isValid, message } = validateConfig(config);
    // DEFER: add more validations here, log helpful warnings, etc.
    // (see https://github.com/ethyca/fides/issues/3171)
    if (!isValid) {
      console.warn("WARN: Configuration file is invalid! Message:", message);
      return;
    }
    return config;
  }
};

/**
 * Load the config.css file from the given URL, or fallback to default filesystem paths.
 *
 * Loading precedence is:
 * 1) Load from `configCssUrl` argument
 * 2) Load from file:///app/config/config.css on filesystem (absolute path)
 * 3) Load from file:./config/config.css on filesystem (relative path)
 *
 * NOTE: The "/app/config" path is for backwards-compatibility with the initial
 * version of ethyca/fides-privacy-center, which expected to always load the
 * configuration file from this well-known path.
 */
export const loadStylesFromFile = async (
  configCssUrl?: string
): Promise<string | undefined> => {
  const urls = [
    configCssUrl,
    "file:///app/config/config.css",
    "file:./config/config.css",
  ];
  const file = await loadConfigFile(urls);
  return file;
};

/**
 * Loads all the ENV variable settings, configuration files, etc. to initialize the environment
 */
// eslint-disable-next-line no-underscore-dangle,@typescript-eslint/naming-convention
export const loadPrivacyCenterEnvironment =
  async (): Promise<PrivacyCenterEnvironment> => {
    if (typeof window !== "undefined") {
      throw new Error(
        "Unexpected error, cannot load server environment from client code!"
      );
    }
    // DEFER: Log a version number here (see https://github.com/ethyca/fides/issues/3171)
    if (process.env.NODE_ENV === "development") {
      console.log("Load Privacy Center environment for session...");
    }

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
      FIDES_DISABLE_BANNER: process.env
        .FIDES_PRIVACY_CENTER__FIDES_DISABLE_BANNER
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
    };

    // Load configuration file (if it exists)
    const config = await loadConfigFromFile(settings.CONFIG_JSON_URL);

    // Load styling file (if it exists)
    const styles = await loadStylesFromFile(settings.CONFIG_CSS_URL);

    // Load client settings (ensuring we only pass-along settings that are safe for the client)
    const clientSettings: PrivacyCenterClientSettings = {
      FIDES_API_URL: settings.FIDES_API_URL,
      SERVER_SIDE_FIDES_API_URL:
        settings.SERVER_SIDE_FIDES_API_URL || settings.FIDES_API_URL,
      DEBUG: settings.DEBUG,
      IS_OVERLAY_ENABLED: settings.IS_OVERLAY_ENABLED,
      IS_PREFETCH_ENABLED: settings.IS_PREFETCH_ENABLED,
      IS_GEOLOCATION_ENABLED: settings.IS_GEOLOCATION_ENABLED,
      GEOLOCATION_API_URL: settings.GEOLOCATION_API_URL,
      OVERLAY_PARENT_ID: settings.OVERLAY_PARENT_ID,
      MODAL_LINK_ID: settings.MODAL_LINK_ID,
      PRIVACY_CENTER_URL: settings.PRIVACY_CENTER_URL,
      FIDES_EMBED: settings.FIDES_EMBED,
      FIDES_DISABLE_SAVE_API: settings.FIDES_DISABLE_SAVE_API,
      FIDES_DISABLE_BANNER: settings.FIDES_DISABLE_BANNER,
      FIDES_TCF_GDPR_APPLIES: settings.FIDES_TCF_GDPR_APPLIES,
      FIDES_STRING: settings.FIDES_STRING,
      IS_FORCED_TCF: settings.IS_FORCED_TCF,
      FIDES_JS_BASE_URL: settings.FIDES_JS_BASE_URL,
      CUSTOM_OPTIONS_PATH: settings.CUSTOM_OPTIONS_PATH,
      PREVENT_DISMISSAL: settings.PREVENT_DISMISSAL,
      ALLOW_HTML_DESCRIPTION: settings.ALLOW_HTML_DESCRIPTION,
      BASE_64_COOKIE: settings.BASE_64_COOKIE,
      FIDES_PRIMARY_COLOR: settings.FIDES_PRIMARY_COLOR,
    };

    // For backwards-compatibility, override FIDES_API_URL with the value from the config file if present
    // DEFER: remove backwards compatibility (see https://github.com/ethyca/fides/issues/1264)
    if (
      config &&
      (config?.server_url_production ||
        config?.server_url_development ||
        (config as any)?.fidesops_host_production ||
        (config as any)?.fidesops_host_development)
    ) {
      console.warn(
        "Using deprecated 'server_url_production' or 'server_url_development' config. " +
          "Please update to using FIDES_PRIVACY_CENTER__FIDES_API_URL environment variable instead."
      );
      const legacyApiUrl =
        process.env.NODE_ENV === "development" ||
        process.env.NODE_ENV === "test"
          ? config.server_url_development ||
            (config as any).fidesops_host_development
          : config.server_url_production ||
            (config as any).fidesops_host_production;

      clientSettings.FIDES_API_URL = legacyApiUrl;
    }

    return {
      settings: clientSettings,
      config,
      styles,
    };
  };
