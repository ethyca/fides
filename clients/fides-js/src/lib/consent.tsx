import { h, render } from "preact";

import {
  ComponentType,
  DeliveryMechanism,
  FidesOptions, UserGeolocation,
} from "./consent-types";
import { debugLog } from "./consent-utils";

import Overlay, { OverlayProps } from "../components/Overlay";
import { getConsentContext } from "./consent-context";
import {getExperience} from "~/services/fides/consent";
import {getGeolocation} from "~/services/external/geolocation";
import {constructLocation} from "~/utils/consent";
import {bindModalLinkToModal, hideModalLink} from "./consent-links";

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
 * Determines if and when to call the API to retrieve geolocation
 */
const retrieveEffectiveGeolocation = async(options: FidesOptions, geolocation: UserGeolocation | undefined): Promise<UserGeolocation | undefined> => {
  let effectiveGeolocation;
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
  return effectiveGeolocation
}

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

  async function renderFidesOverlay(): Promise<void> {
    try {
      debugLog(
        options.debug,
        "Rendering Fides overlay CSS & HTML into the DOM..."
      );
      let effectiveGeolocation = geolocation;
      let effectiveExperience = experience;

      if (!experience) {
        // If experience is not provided, we need to retrieve it via the Fides API.
        // In order to retrieve it, we first need a valid geolocation, which is either provided
        // OR can be obtained via the Fides API
        effectiveGeolocation = await retrieveEffectiveGeolocation(options, geolocation)
        const userLocationString = constructLocation(effectiveGeolocation);
        if (!userLocationString) {
          throw new Error(
              `User location could not be constructed from location params: ${effectiveGeolocation}.`
          );
        }
        effectiveExperience = await getExperience(userLocationString, options.debug);
        if (!effectiveExperience) {
          debugLog(
            options.debug,
            `No relevant experience found.`
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
