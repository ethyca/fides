import { h, render } from "preact";

import { ComponentType } from "./consent-types";
import { debugLog, hasActionNeededNotices } from "./consent-utils";

import Overlay, { OverlayProps } from "../components/Overlay";

/**
 * Initialize the Fides Consent overlay components.
 *
 * (see the type definition of FidesOptions for what options are available)
 */
export const initOverlay = async ({
  experience,
  fidesRegionString,
  cookie,
  options,
}: OverlayProps): Promise<void> => {
  debugLog(options.debug, "Initializing Fides consent overlays...");

  async function renderFidesOverlay(): Promise<void> {
    try {
      debugLog(
        options.debug,
        "Rendering Fides overlay CSS & HTML into the DOM..."
      );

      // Find or create the parent element where we should insert the overlay
      const overlayParentId = options.overlayParentId || "fides-overlay";
      let parentElem = document.getElementById(overlayParentId);
      if (!parentElem) {
        debugLog(
          options.debug,
          `Parent element not found (#${overlayParentId}), creating and appending to body...`
        );
        // Create our own parent element and append to body
        parentElem = document.createElement("div");
        parentElem.id = overlayParentId;
        document.body.appendChild(parentElem);
      }

      if (experience.component === ComponentType.OVERLAY) {
        // Render the Overlay to the DOM!
        render(
          <Overlay
            options={options}
            experience={experience}
            cookie={cookie}
            fidesRegionString={fidesRegionString}
          />,
          parentElem
        );
        debugLog(options.debug, "Fides overlay is now showing!");
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
