import { h, render } from "preact";

import { ComponentType, DeliveryMechanism } from "./consent-types";
import { debugLog } from "./consent-utils";

import Overlay, { OverlayProps } from "../components/Overlay";
import { showModalLinkAndSetOnClick } from "./consent-links";

/**
 * Initialize the Fides Consent overlay components.
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
  async function renderFidesOverlay(): Promise<void> {
    try {
      debugLog(
        options.debug,
        "Rendering Fides overlay CSS & HTML into the DOM... (updated!)"
      );

      // TODO: clean this up
      const rootElementId = "fides-overlay";
      let root = document.getElementById(rootElementId);
      if (!root) {
        debugLog(
          options.debug,
          "Root #fides-overlay not found, inserting before rendering..."
        );
        // Create our own root element and append to body first
        root = document.createElement("div");
        root.id = rootElementId;
        document.body.appendChild(root);
      }

      if (experience.component === ComponentType.OVERLAY) {
        if (experience.delivery_mechanism === DeliveryMechanism.BANNER) {
          // Render the Overlay to the DOM!
          render(
            <Overlay
              consentDefaults={consentDefaults}
              options={options}
              experience={experience}
              geolocation={geolocation}
            />,
            root
          );
          debugLog(options.debug, "Fides overlay is now showing!");
        } else if (experience.delivery_mechanism === DeliveryMechanism.LINK) {
          showModalLinkAndSetOnClick(options.debug);
        }
      }
      return await Promise.resolve();
    } catch (e) {
      debugLog(options.debug, e);
      return Promise.reject(e);
    }
  }

  // Ensure we only render the overlay to the DOM once it's loaded
  if (document?.readyState !== "complete") {
    debugLog(options.debug, "DOM not loaded, adding event listener");
    document.addEventListener("readystatechange", async () => {
      if (document.readyState === "complete") {
        debugLog(options.debug, "DOM fully loaded and parsed");
        await renderFidesOverlay();
      }
    });
  } else {
    await renderFidesOverlay();
  }

  return Promise.resolve();
};
