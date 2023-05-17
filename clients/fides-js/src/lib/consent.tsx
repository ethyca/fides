import { h, render } from "preact";

import {
  ComponentType,
  DeliveryMechanism,
  FIDES_MODAL_LINK,
  FidesOptions,
  UserGeolocation,
} from "./consent-types";
import { debugLog } from "./consent-utils";

import Overlay, { OverlayProps } from "../components/Overlay";
import { getConsentContext } from "./consent-context";

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
  geoLocation?: UserGeolocation,
  debug: boolean = false
): string | null => {
  debugLog(debug, "constructing geolocation...");
  if (!geoLocation) {
    debugLog(
      debug,
      "cannot construct user location since geoLocation is undefined"
    );
    return null;
  }
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
const getGeolocation = async (
  geolocationApiUrl?: string,
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
 * Hide pre-existing link in the DOM if we do not need to trigger a modal
 */
const hideModalLink = (debug: boolean): void => {
  // TODO- it's possible that this element does not exist by the time this method runs
  const modalLinkEl: HTMLElement | null =
    document.getElementById(FIDES_MODAL_LINK);
  if (modalLinkEl) {
    debugLog(debug, "modal link element exists, attempting to hide it");
    // TODO: hide link
    // eslint-disable-next-line no-param-reassign
    modalLinkEl.style.display = "none";
  }
  debugLog(
    debug,
    "modal link element does not exist, so there is nothing to hide"
  );
};

/**
 * Update the pre-existing modal link in the DOM to trigger the modal
 */
const bindModalLinkToModal = (debug: boolean): void => {
  // TODO- it's possible that this element does not exist by the time this method runs
  const modalLinkEl: HTMLElement | null =
    document.getElementById(FIDES_MODAL_LINK);
  if (
    modalLinkEl &&
    // TODO: does this need to be an HTMLAnchorElement?
    modalLinkEl instanceof HTMLAnchorElement
  ) {
    debugLog(
      debug,
      `Fides modal link element found, updating click event to trigger modal`
    );
    modalLinkEl.onclick = () => {
      // TODO: render modal component
    };
  } else {
    throw new Error("Fides modal link element could not be found");
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
    "Validating Fides consent overlay options...",
    options
  );
  if (!validateOptions(options)) {
    hideModalLink(options.debug);
    return Promise.reject(new Error("Invalid overlay options"));
  }

  if (options.isOverlayDisabled) {
    debugLog(
      options.debug,
      "Fides consent overlay is disabled, skipping overlay initialization!"
    );
    hideModalLink(options.debug);
    return Promise.resolve();
  }

  if (experience && experience.component !== ComponentType.OVERLAY) {
    hideModalLink(options.debug);
    return Promise.resolve();
  }

  async function getExperience(userLocationString: String) {
    debugLog(
      options.debug,
      "Fetching experience where component === privacy_center...",
      userLocationString
    );
    // TODO: GET experience using location and user id (if exists)
    return undefined;
  }

  async function renderFidesOverlay(): Promise<void> {
    try {
      debugLog(
        options.debug,
        "Rendering Fides overlay CSS & HTML into the DOM..."
      );
      let effectiveGeolocation = geolocation;
      let effectiveExperience = experience;

      if (!experience) {
        if (!constructLocation(geolocation)) {
          if (options.isGeolocationEnabled) {
            effectiveGeolocation = await getGeolocation(
              options.geolocationApiUrl,
              options.debug
            );
          } else {
            throw new Error(
              `User location is required but could not be retrieved because geolocation is disabled.`
            );
          }
        }
        const userLocationString = constructLocation(effectiveGeolocation);
        if (!userLocationString) {
          throw new Error(
            `User location could not be constructed from location params: ${effectiveGeolocation}.`
          );
        }
        effectiveExperience = await getExperience(userLocationString);
        if (!effectiveExperience) {
          debugLog(
            options.debug,
            `No relevant experience found based on user location.`,
            userLocationString
          );
          hideModalLink(options.debug);
          return await Promise.resolve();
        }
      }

      if (
        !effectiveExperience?.privacy_notices ||
        effectiveExperience.privacy_notices.length === 0
      ) {
        debugLog(
          options.debug,
          `No relevant notices in the privacy experience.`,
          effectiveExperience
        );
        hideModalLink(options.debug);
        return await Promise.resolve();
      }

      if (getConsentContext().globalPrivacyControl && effectiveExperience) {
        effectiveExperience.privacy_notices.forEach((notice) => {
          if (notice.has_gpc_flag) {
            // todo- send consent request downstream automatically with PATCH {{host}}/privacy-preferences
          }
        });
      }

      if (
        effectiveExperience &&
        effectiveExperience.component === ComponentType.OVERLAY
      ) {
        if (
          effectiveExperience.delivery_mechanism ===
          DeliveryMechanism.BANNER
        ) {
          hideModalLink(options.debug);
          // Render the Overlay to the DOM!
          render(
            <Overlay
              consentDefaults={consentDefaults}
              options={options}
              experience={experience}
              geolocation={effectiveGeolocation}
            />,
            document.body
          );
          debugLog(options.debug, "Fides overlay is now showing!");
        } else if (
          effectiveExperience.delivery_mechanism ===
          DeliveryMechanism.LINK
        ) {
          bindModalLinkToModal(options.debug);
        }
      } else {
        hideModalLink(options.debug);
      }
      return await Promise.resolve();
    } catch (e) {
      hideModalLink(options.debug);
      debugLog(options.debug, e);
      return Promise.reject(e);
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
