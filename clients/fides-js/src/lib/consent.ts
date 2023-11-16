import { ContainerNode } from "preact";

import { ComponentType } from "./consent-types";
import { debugLog } from "./consent-utils";

import { OverlayProps } from "../components/types";

const FIDES_EMBED_CONTAINER_ID = "fides-embed-container";
const FIDES_OVERLAY_DEFAULT_ID = "fides-overlay";

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
  renderOverlay,
}: OverlayProps & {
  renderOverlay: (props: OverlayProps, parent: ContainerNode) => void;
}): Promise<void> => {
  debugLog("Initializing Fides consent overlays...");

  async function renderFidesOverlay(): Promise<void> {
    try {
      debugLog("Rendering Fides overlay CSS & HTML into the DOM...");

      let parentElem;
      if (options.fidesEmbed) {
        // Embed mode requires an existing element by which to embed the consent overlay
        parentElem = document.getElementById(FIDES_EMBED_CONTAINER_ID);
        if (!parentElem) {
          throw new Error(
            "Element with id fides-embed-container could not be found."
          );
        }
      } else {
        // Find or create the parent element where we should insert the overlay
        const overlayParentId =
          options.overlayParentId || FIDES_OVERLAY_DEFAULT_ID;
        parentElem = document.getElementById(overlayParentId);
        if (!parentElem) {
          debugLog(
            `Parent element not found (#${overlayParentId}), creating and appending to body...`
          );
          // Create our own parent element and append to body
          parentElem = document.createElement("div");
          parentElem.id = overlayParentId;
          document.body.prepend(parentElem);
        }
      }

      if (
        experience.component === ComponentType.OVERLAY ||
        experience.component === ComponentType.TCF_OVERLAY
      ) {
        // Render the Overlay to the DOM!
        renderOverlay(
          { experience, fidesRegionString, cookie, options },
          parentElem
        );
        debugLog("Fides overlay is now showing!");
      }
      return await Promise.resolve();
    } catch (e) {
      debugLog(e);
      return Promise.reject(e);
    }
  }

  // Ensure we only render the overlay to the DOM once it's loaded
  if (document?.readyState !== "complete") {
    debugLog("DOM not loaded, adding event listener");
    document.addEventListener("readystatechange", async () => {
      if (document.readyState === "complete") {
        debugLog("DOM fully loaded and parsed");
        await renderFidesOverlay();
      }
    });
  } else {
    await renderFidesOverlay();
  }

  return Promise.resolve();
};
