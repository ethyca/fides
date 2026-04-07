/* eslint-disable no-console */
/**
 * Utility functions and logic that is designed to exclusively run server-side to configure the environment for the app, e.g.:
 * 1) Securely loading ENV variables for the client to use
 * 2) Fetching configuration files (config.json, config.css) to inject into the client
 * 3) etc.
 *
 * During server-side rendering, call loadPrivacyCenterEnvironment() to initialize the environment values for the App.
 */
import type { AttributionOptions } from "fides-js";
import { URL } from "url";

import loadEnvironmentVariables from "~/app/server-utils/loadEnvironmentVariables";
import { PrivacyCenterSettings } from "~/app/server-utils/PrivacyCenterSettings";
import { transformConfig, validateConfig } from "~/common/validation";
import { Property } from "~/types/api";
import { PrivacyCenterConfig } from "~/types/api/models/PrivacyCenterConfig";
import { Config } from "~/types/config";

/**
 * Subset of PrivacyCenterSettings that are for use only on server-side and
 * should never be exposed to the client.
 */

export type PrivacyCenterServerSettings = Pick<
  PrivacyCenterSettings,
  | "SERVER_SIDE_FIDES_API_URL"
  | "FIDES_JS_MAX_AGE_SECONDS"
  | "FIDES_JS_SERVE_STALE_SECONDS"
  | "MISSING_EXPERIENCE_BEHAVIOR"
  | "LOG_LEVEL"
>;

/**
 * Subset of PrivacyCenterSettings that are forwarded to the client.
 *
 * NOTE: Since these are exposed on the client, they cannot contain any secrets!
 */
export type PrivacyCenterClientSettings = Pick<
  PrivacyCenterSettings,
  | "FIDES_API_URL"
  | "DEBUG"
  | "GEOLOCATION_API_URL"
  | "IS_GEOLOCATION_ENABLED"
  | "IS_OVERLAY_ENABLED"
  | "IS_PREFETCH_ENABLED"
  | "OVERLAY_PARENT_ID"
  | "MODAL_LINK_ID"
  | "PRIVACY_CENTER_URL"
  | "SHOW_BRAND_LINK"
  | "FIDES_EMBED"
  | "FIDES_DISABLE_SAVE_API"
  | "FIDES_DISABLE_NOTICES_SERVED_API"
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
  | "FIDES_CLEAR_COOKIE"
  | "FIDES_CONSENT_OVERRIDE"
  | "FIDES_DISABLED_NOTICES"
  | "FIDES_DISABLED_SYSTEMS"
  | "FIDES_CONSENT_NON_APPLICABLE_FLAG_MODE"
  | "FIDES_CONSENT_FLAG_TYPE"
  | "FIDES_INITIALIZED_EVENT_MODE"
  | "FIDES_UNSUPPORTED_REPEATED_SCRIPT_LOADING"
  | "FIDES_COOKIE_SUFFIX"
  | "FIDES_COOKIE_COMPRESSION"
  | "ATTRIBUTION_ENABLED"
  | "ATTRIBUTION_ANCHOR_TEXT"
  | "ATTRIBUTION_DESTINATION_URL"
  | "ATTRIBUTION_NOFOLLOW"
>;

export type Styles = string;

/**
 * Environment that is generated server-side and provided to the client
 */
export interface PrivacyCenterEnvironment {
  settings: PrivacyCenterClientSettings;
  config?: Config | PrivacyCenterConfig;
  styles?: Styles;
  property?: Property | null;
  location?: {
    country?: string;
    location?: string;
    region?: string;
  };
}

/**
 * Load a config file from the given list of URLs, trying them in order until one is successfully read.
 */
/* eslint-disable consistent-return */
const loadConfigFile = async (
  urls: (string | undefined)[],
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
          `Config file URLs currently must use the 'file:' protocol: ${urlString}`,
        );
      }
      // Relative paths (e.g. "file:./") aren't supported by node's URL class.
      // So to support this, we just use a path string instead!
      let path;
      if (urlString.startsWith("file:.")) {
        path = urlString.replace("file:", "");
      }
      const file = await fsPromises.readFile(path || url, "utf-8");
      console.debug(`Loaded configuration file: ${urlString}`);
      return file;
    } catch (err: any) {
      // Catch "file not found" errors (ENOENT)
      if (err.code === "ENOENT") {
        continue;
      }
      // Log everything else and continue
      console.error(
        `Failed to load configuration file from ${urlString}. Error: `,
        err,
      );
    }
  }
  /* eslint-enable no-restricted-syntax,no-continue,no-await-in-loop */
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
  configJsonUrl?: string,
): Promise<Config | undefined> => {
  const urls = [
    configJsonUrl,
    "file:///app/config/config.json",
    "file:./config/config.json",
  ];
  const file = await loadConfigFile(urls);
  if (file) {
    const parsedConfig = JSON.parse(file);
    const { isValid, message } = validateConfig(parsedConfig);
    if (!isValid) {
      throw new Error(
        `Privacy Center configuration is invalid and cannot start: ${message}`,
      );
    }
    const config = transformConfig(parsedConfig);
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
  configCssUrl?: string,
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
 * Load server settings from global environment variables
 * The returned Server settings should never be exposed to the client
 */
export const loadServerSettings = (): PrivacyCenterServerSettings => {
  const settings = loadEnvironmentVariables();
  const serverSideSettings: PrivacyCenterServerSettings = {
    SERVER_SIDE_FIDES_API_URL:
      settings.SERVER_SIDE_FIDES_API_URL || settings.FIDES_API_URL,
    FIDES_JS_MAX_AGE_SECONDS: settings.FIDES_JS_MAX_AGE_SECONDS,
    FIDES_JS_SERVE_STALE_SECONDS: settings.FIDES_JS_SERVE_STALE_SECONDS,
    MISSING_EXPERIENCE_BEHAVIOR: settings.MISSING_EXPERIENCE_BEHAVIOR,
    LOG_LEVEL: settings.LOG_LEVEL,
  };

  return serverSideSettings;
};

export const getFidesApiUrl = () => {
  const settings = loadEnvironmentVariables();
  return settings.SERVER_SIDE_FIDES_API_URL || settings.FIDES_API_URL;
};

/**
 * Returns the env variables that should be shared with the client
 */
export const getClientSettings = (): PrivacyCenterClientSettings => {
  // Load environment variables
  const settings = loadEnvironmentVariables();

  // Load client settings (ensuring we only pass-along settings that are safe for the client)
  const clientSettings: PrivacyCenterClientSettings = {
    FIDES_API_URL: settings.FIDES_API_URL,
    DEBUG: settings.DEBUG,
    IS_OVERLAY_ENABLED: settings.IS_OVERLAY_ENABLED,
    IS_PREFETCH_ENABLED: settings.IS_PREFETCH_ENABLED,
    IS_GEOLOCATION_ENABLED: settings.IS_GEOLOCATION_ENABLED,
    GEOLOCATION_API_URL: settings.GEOLOCATION_API_URL,
    OVERLAY_PARENT_ID: settings.OVERLAY_PARENT_ID,
    MODAL_LINK_ID: settings.MODAL_LINK_ID,
    PRIVACY_CENTER_URL: settings.PRIVACY_CENTER_URL,
    SHOW_BRAND_LINK: settings.SHOW_BRAND_LINK,
    FIDES_EMBED: settings.FIDES_EMBED,
    FIDES_DISABLE_SAVE_API: settings.FIDES_DISABLE_SAVE_API,
    FIDES_DISABLE_NOTICES_SERVED_API: settings.FIDES_DISABLE_NOTICES_SERVED_API,
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
    FIDES_CLEAR_COOKIE: settings.FIDES_CLEAR_COOKIE,
    FIDES_CONSENT_OVERRIDE: settings.FIDES_CONSENT_OVERRIDE,
    FIDES_DISABLED_NOTICES: settings.FIDES_DISABLED_NOTICES,
    FIDES_DISABLED_SYSTEMS: settings.FIDES_DISABLED_SYSTEMS,
    FIDES_CONSENT_NON_APPLICABLE_FLAG_MODE:
      settings.FIDES_CONSENT_NON_APPLICABLE_FLAG_MODE,
    FIDES_CONSENT_FLAG_TYPE: settings.FIDES_CONSENT_FLAG_TYPE,
    FIDES_INITIALIZED_EVENT_MODE: settings.FIDES_INITIALIZED_EVENT_MODE,
    FIDES_UNSUPPORTED_REPEATED_SCRIPT_LOADING:
      settings.FIDES_UNSUPPORTED_REPEATED_SCRIPT_LOADING,
    FIDES_COOKIE_SUFFIX: settings.FIDES_COOKIE_SUFFIX,
    FIDES_COOKIE_COMPRESSION: settings.FIDES_COOKIE_COMPRESSION,
    ATTRIBUTION_ENABLED: settings.ATTRIBUTION_ENABLED,
    ATTRIBUTION_ANCHOR_TEXT: settings.ATTRIBUTION_ANCHOR_TEXT,
    ATTRIBUTION_DESTINATION_URL: settings.ATTRIBUTION_DESTINATION_URL,
    ATTRIBUTION_NOFOLLOW: settings.ATTRIBUTION_NOFOLLOW,
  };

  return clientSettings;
};

export const buildAttributionOptions = (
  settings: PrivacyCenterClientSettings,
): AttributionOptions | undefined =>
  settings.ATTRIBUTION_ENABLED
    ? {
        anchorText: settings.ATTRIBUTION_ANCHOR_TEXT,
        destinationUrl: settings.ATTRIBUTION_DESTINATION_URL,
        nofollow: settings.ATTRIBUTION_NOFOLLOW,
      }
    : undefined;
