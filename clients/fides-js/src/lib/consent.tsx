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
 * Construct user geolocation str to be ingested by Fides API
 * Returns null if geolocation cannot be constructed by provided params
 */
const constructLocation = (
  debug: boolean,
  geoLocation: UserGeolocation
): string | null => {
  debugLog(debug, "validating getLocation...");
  if (geoLocation.location) {
    return geoLocation.location;
  }
  if (geoLocation.country && geoLocation.region) {
    return `${geoLocation.country}-${geoLocation.region}`;
  }
  debugLog(
    debug,
    "cannot construct user location from provided geoLocation params..."
  );
  return null;
};

/**
 * Fetch the user's geolocation from an external API
 */
const getLocation = async (options: FidesOptions): Promise<UserGeolocation> => {
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

  async function afterDomIsLoaded() {
    debugLog(config.options.debug, "DOM fully loaded and parsed");

    try {
      debugLog(
        config.options.debug,
        "Adding Fides consent banner CSS & HTML into the DOM..."
      );
      let userLocation: UserGeolocation | undefined = config.geolocation;
      if (
        !config.experience &&
        !userLocation &&
        config.options.isGeolocationEnabled
      ) {
        userLocation = await getLocation(config.options);
        if (constructLocation(config.options.debug, userLocation)) {
          // todo- get applicable notices using geoLocation
          debugLog(config.options.debug, "User location found.", userLocation);
        } else {
          debugLog(
            config.options.debug,
            "User location could not be constructed from location params.",
            userLocation
          );
        }
      } else {
        debugLog(
          config.options.debug,
          "Geolocation must be enabled if config.geolocation is not provided!"
        );
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
  }
  if (document?.readyState !== "complete") {
    debugLog(config.options.debug, "DOM not loaded, adding event listener");
    document.addEventListener("DOMContentLoaded", async () => {
      await afterDomIsLoaded();
    });
  } else {
    await afterDomIsLoaded();
  }

  return Promise.resolve();
};
