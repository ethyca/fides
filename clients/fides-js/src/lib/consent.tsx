import { h, render } from "preact";

import { FidesConfig, FidesOptions, UserGeolocation } from "./consent-types";
import { debugLog } from "./consent-utils";

import App from "../components/App";

/**
 * Validate the config options
 */
const validateBannerOptions = (config: FidesConfig): boolean => {
  // Check if options is an invalid type
  if (config.options === undefined || typeof config.options !== "object") {
    return false;
  }
  // todo- more validation here?

  if (!config.options.privacyCenterUrl) {
    debugLog(
      config.options.debug,
      "Invalid banner options: privacyCenterUrl is required!"
    );
    return false;
  }

  if (config.options.privacyCenterUrl) {
    try {
      // eslint-disable-next-line no-new
      new URL(config.options.privacyCenterUrl);
    } catch (e) {
      debugLog(
        config.options.debug,
        "Invalid banner options: privacyCenterUrl is an invalid URL!",
        config
      );
      return false;
    }
  }

  return true;
};

/**
 * Fetch the user's geolocation from an external API
 */
const getLocation = async (options: FidesOptions): Promise<UserGeolocation> => {
  // assumes that isGeolocationEnabled is true
  debugLog(options.debug, "Running getLocation...");
  const { geolocationApiUrl } = options;

  if (!geolocationApiUrl) {
    debugLog(
      options.debug,
      "Location cannot be found due to no configured geoLocationApiUrl."
    );
    return {};
  }

  debugLog(
    options.debug,
    `Calling geolocation API: GET ${geolocationApiUrl}...`
  );
  const fetchOptions: RequestInit = {
    mode: "cors",
  };
  const response = await fetch(geolocationApiUrl, fetchOptions);

  if (!response.ok) {
    debugLog(
      options.debug,
      "Error getting location from geolocation API, returning {}. Response:",
      response
    );
    return {};
  }

  try {
    const body = await response.json();
    debugLog(
      options.debug,
      "Got location response from geolocation API, returning:",
      body
    );
    return body;
  } catch (e) {
    debugLog(
      options.debug,
      "Error parsing response body from geolocation API, returning {}. Response:",
      response
    );
    return {};
  }
};

/**
 * Initialize the Fides Consent overlay components.
 *
 * Includes fetching location and experience, if not provided, setting up banner and modal,
 * showing/hiding links, and showing/hiding the banner.
 *
 * (see the type definition of ConsentBannerOptions for what options are available)
 */
export const initOverlay = async (config: FidesConfig): Promise<void> => {
  debugLog(config.options.debug, "Initializing Fides consent overlays...");

  debugLog(
    config.options.debug,
    "Validating Fides consent banner options...",
    config.options
  );
  if (!validateBannerOptions(config)) {
    return Promise.reject(new Error("Invalid banner options"));
  }

  if (config.options.isOverlayDisabled) {
    debugLog(
      config.options.debug,
      "Fides consent banner is disabled, skipping banner initialization!"
    );
    return Promise.resolve();
  }

  document.addEventListener("DOMContentLoaded", () => {
    debugLog(config.options.debug, "DOM fully loaded and parsed");

    try {
      debugLog(
        config.options.debug,
        "Adding Fides consent banner CSS & HTML into the DOM..."
      );
      if (config.options.isGeolocationEnabled) {
        getLocation(config.options)
          .then(() => {
            // todo- get applicable notices using location
          })
          .catch(() => {
            // if something goes wrong with location api, we still want to render notices
          });
      }

      render(<App config={config} />, document.body);
      const consentLinkEl = document.getElementById("fides-consent-link");
      if (
        consentLinkEl &&
        consentLinkEl instanceof HTMLAnchorElement &&
        config.options.privacyCenterUrl
      ) {
        debugLog(
          config.options.debug,
          `Fides consent link el found, replacing href with ${config.options.privacyCenterUrl}`
        );
        consentLinkEl.href = config.options.privacyCenterUrl;
        // TODO: depending on notices / experience config, we update onclick of this link to nav to PC or open modal,
        // or hide link entirely
      } else {
        debugLog(config.options.debug, "Fides consent link el not found");
      }

      debugLog(config.options.debug, "Fides consent banner is now showing!");
    } catch (e) {
      debugLog(config.options.debug, e);
    }
  });
  return Promise.resolve();
};
