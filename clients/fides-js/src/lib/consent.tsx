import { h, render } from "preact";

import { FidesOptions, UserGeolocation } from "./consent-types";
import { debugLog } from "./consent-utils";

import Overlay, { OverlayProps } from "../components/Overlay";

/**
 * Validate the config options
 */
const validateOptions = (options: FidesOptions): boolean => {
  // Check if options is an invalid type
  if (options === undefined || typeof options !== "object") {
    return false;
  }
  // todo- more validation here?

  if (!options.privacyCenterUrl) {
    debugLog(options.debug, "Invalid options: privacyCenterUrl is required!");
    return false;
  }

  if (options.privacyCenterUrl) {
    try {
      // eslint-disable-next-line no-new
      new URL(options.privacyCenterUrl);
    } catch (e) {
      debugLog(
        options.debug,
        "Invalid options: privacyCenterUrl is an invalid URL!",
        options.privacyCenterUrl
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
  geoLocation: UserGeolocation,
  debug: boolean = false
): string | null => {
  debugLog(debug, "validating getLocation...");
  if (geoLocation.location) {
    return geoLocation.location;
  }
  if (geoLocation.country && geoLocation.region) {
    return `${geoLocation.country}-${geoLocation.region}`;
  }
  if (geoLocation.country) {
    return geoLocation.country;
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
const getLocation = async (
  geolocationApiUrl: string,
  debug: boolean = false
): Promise<UserGeolocation> => {
  debugLog(debug, "Running getLocation...");

  if (!geolocationApiUrl) {
    debugLog(
      debug,
      "Location cannot be found due to no configured geoLocationApiUrl."
    );
    return {};
  }

  debugLog(debug, `Calling geolocation API: GET ${geolocationApiUrl}...`);
  const fetchOptions: RequestInit = {
    mode: "cors",
  };
  const response = await fetch(geolocationApiUrl, fetchOptions);

  if (!response.ok) {
    debugLog(
      debug,
      "Error getting location from geolocation API, returning {}. Response:",
      response
    );
    return {};
  }

  try {
    const body = await response.json();
    debugLog(
      debug,
      "Got location response from geolocation API, returning:",
      body
    );
    return body;
  } catch (e) {
    debugLog(
      debug,
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
export const initOverlay = async ({
  consentDefaults,
  experience,
  geolocation,
  options,
}: OverlayProps): Promise<void> => {
  debugLog(options.debug, "Initializing Fides consent overlays...");

  debugLog(
    options.debug,
    "Validating Fides consent banner options...",
    options
  );
  if (!validateOptions(options)) {
    return Promise.reject(new Error("Invalid banner options"));
  }

  if (options.isOverlayDisabled) {
    debugLog(
      options.debug,
      "Fides consent banner is disabled, skipping banner initialization!"
    );
    return Promise.resolve();
  }

  async function renderFidesOverlay() {
    try {
      debugLog(
        options.debug,
        "Rending Fides overlay CSS & HTML into the DOM..."
      );

      // Fetch the user location (if not pre-loaded)
      let userLocation: UserGeolocation | undefined = geolocation;
      if (
        !userLocation &&
        options.isGeolocationEnabled &&
        options.geolocationApiUrl
      ) {
        userLocation = await getLocation(
          options.geolocationApiUrl,
          options.debug
        );
        if (constructLocation(userLocation, options.debug)) {
          // todo- get applicable notices using geoLocation
          debugLog(options.debug, "User location found.", userLocation);
        } else {
          debugLog(
            options.debug,
            "User location could not be constructed from location params.",
            userLocation
          );
        }
      } else {
        debugLog(
          options.debug,
          "Geolocation must be enabled if config.geolocation is not provided!"
        );
      }

      // Render the Overlay to the DOM!
      render(
        <Overlay
          consentDefaults={consentDefaults}
          options={options}
          experience={experience}
          geolocation={userLocation}
        />,
        document.body
      );
      debugLog(options.debug, "Fides overlay is now showing!");

      // Look for a "#fides-consent-link" element in the DOM and update it to link to the Privacy Center
      // DEFER: Revisit whether or not this "link" logic is needed
      const consentLinkEl = document.getElementById("fides-consent-link");
      if (
        consentLinkEl &&
        consentLinkEl instanceof HTMLAnchorElement &&
        options.privacyCenterUrl
      ) {
        debugLog(
          options.debug,
          `Fides consent link el found, replacing href with ${options.privacyCenterUrl}`
        );
        consentLinkEl.href = options.privacyCenterUrl;
        // TODO: depending on notices / experience config, we update onclick of this link to nav to PC or open modal,
        // or hide link entirely
      } else {
        debugLog(options.debug, "Fides consent link el not found");
      }
    } catch (e) {
      debugLog(options.debug, e);
    }
  }

  // Ensure we only render the overlay to the DOM once it's loaded
  if (document?.readyState !== "complete") {
    debugLog(options.debug, "DOM not loaded, adding event listener");
    document.addEventListener("DOMContentLoaded", async () => {
      debugLog(options.debug, "DOM fully loaded and parsed");
      await renderFidesOverlay();
    });
  } else {
    await renderFidesOverlay();
  }

  return Promise.resolve();
};
