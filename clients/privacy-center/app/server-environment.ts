/* eslint-disable no-console,consistent-return */
/**
 * Utility functions and logic that is designed to exclusively run server-side to configure the environment for the app, e.g.:
 * 1) Securely loading ENV variables for the client to use
 * 2) Fetching configuration files (config.json, config.css) to inject into the client
 * 3) etc.
 *
 * During server-side rendering, call loadPrivacyCenterEnvironment() to initialize the environment values for the App.
 *
 * On the client-side, call the usePrivacyCenterEnvironment() hook in code to safely access the environment values at runtime.
 */
import { URL } from "url";

import { Config } from "~/types/config";

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
  FIDES_API_URL: string; // e.g. http://localhost:8080/api/v1
  CONFIG_JSON_URL: string; // e.g. file:///app/config/config.json
  CONFIG_CSS_URL: string; // e.g. file:///app/config/config.css
}

/**
 * Environment that is generated server-side and provided to the client
 */
export interface PrivacyCenterEnvironment {
  fidesApiUrl: string;
  config?: Config;
  styles?: string;
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
      console.log(`Loaded configuration file: ${urlString}`);
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
    const config = JSON.parse(file) as Config;
    // DEFER: validate the configuration here, log helpful warnings, etc.
    // (see https://github.com/ethyca/fides/issues/3171)
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
let _environment: PrivacyCenterEnvironment;
export const loadPrivacyCenterEnvironment =
  async (): Promise<PrivacyCenterEnvironment> => {
    if (typeof window !== "undefined") {
      throw new Error(
        "Unexpected error, cannot load server environment from client code!"
      );
    }
    // DEFER: Log a version number here (see https://github.com/ethyca/fides/issues/3171)
    console.log("Load Privacy Center environment for session...");

    // Load environment variables
    const settings: PrivacyCenterSettings = {
      FIDES_API_URL:
        process.env.FIDES_PRIVACY_CENTER__FIDES_API_URL ||
        "http://localhost:8080/api/v1",
      CONFIG_JSON_URL:
        process.env.FIDES_PRIVACY_CENTER__CONFIG_JSON_URL ||
        "file:///app/config/config.json",
      CONFIG_CSS_URL:
        process.env.FIDES_PRIVACY_CENTER__CONFIG_CSS_URL ||
        "file:///app/config/config.css",
    };

    // Load configuration file (if it exists)
    const config = await loadConfigFromFile(settings.CONFIG_JSON_URL);

    // Load styling file (if it exists)
    const styles = await loadStylesFromFile(settings.CONFIG_CSS_URL);

    // Initialize the _environment variable, so usePrivacyCenterEnvironment() can be used
    _environment = {
      fidesApiUrl: settings.FIDES_API_URL,
      config,
      styles,
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

      _environment.fidesApiUrl = legacyApiUrl;
    }

    return _environment;
  };

/**
 * CLIENT-SIDE functions
 */

/**
 * Hydrate the environment on the client-side, given a serverEnvironment
 * argument that should have been received from - you guessed it - the server!
 */
export const hydratePrivacyCenterEnvironment = (
  serverEnvironment?: PrivacyCenterEnvironment
): PrivacyCenterEnvironment => {
  // DEFER: handle this (see https://github.com/ethyca/fides/issues/3212)
  if (_environment) {
    console.warn(
      "Called hydratePrivacyCenterEnvironment() after environment was already initialized!"
    );
  }
  if (serverEnvironment) {
    _environment = serverEnvironment;
  }
  return _environment;
};

/**
 * Basic hook for client-side code to safely access the configured environment.
 */
export const getPrivacyCenterEnvironment = (): PrivacyCenterEnvironment => {
  if (!_environment) {
    throw new Error(
      "Called usePrivacyCenterEnvironment() prior to initializing with hydratePrivacyCenterEnvironment()!"
    );
  }
  return _environment;
};
