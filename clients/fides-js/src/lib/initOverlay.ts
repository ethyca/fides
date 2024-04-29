import { ContainerNode, render } from "preact";

import { ComponentType } from "./consent-types";
import { debugLog } from "./consent-utils";

import { OverlayProps } from "../components/types";
import { ColorFormat, generateLighterColor } from "./style-utils";

const FIDES_EMBED_CONTAINER_ID = "fides-embed-container";
const FIDES_OVERLAY_DEFAULT_ID = "fides-overlay";

/**
 * Save a reference to the parent element used to render the overlay. This
 * allows us to detect re-renders and defensively unmount previous versions of
 * the overlay from the DOM if this occurs.
 */
let renderedParentElem: ContainerNode | undefined;

/**
 * Initialize the Fides Consent overlay components.
 *
 * (see the type definition of FidesOptions for what options are available)
 */
export const initOverlay = async ({
  options,
  experience,
  i18n,
  fidesRegionString,
  cookie,
  savedConsent,
  renderOverlay,
}: OverlayProps & {
  renderOverlay: (props: OverlayProps, parent: ContainerNode) => void;
}): Promise<void> => {
  debugLog(options.debug, "Initializing Fides consent overlays...");

  async function renderFidesOverlay(): Promise<void> {
    try {
      debugLog(
        options.debug,
        "Rendering Fides overlay CSS & HTML into the DOM..."
      );

      // If this function is called multiple times (e.g. due to calling
      // Fides.reinitialize() or similar), first ensure we unmount any
      // previously rendered instances
      if (renderedParentElem) {
        debugLog(
          options.debug,
          "Detected that Fides overlay was previously rendered! Unmounting previous instance from the DOM."
        );

        /**
         * Render a `null` VDOM component to unmount any existing tree. The use
         * of `null` here isn't explicitly mentioned in the Preact docs[1], but
         * the maintainers have commented on StackOverflow[1] and rely on this
         * behaviour to implement a React-compatible `unmountComponentAtNode`[3]
         * function, so this should be safe to rely on.
         *
         * [1]: https://preactjs.com/guide/v10/api-reference/#render
         * [2]: https://stackoverflow.com/questions/50946950/how-to-destroy-root-preact-node
         * [3]: https://github.com/preactjs/preact/blob/3123e7f0a98ff15f5b14a2b764ddd036e79cd926/compat/src/index.js#L100
         */
        render(null, renderedParentElem);
        renderedParentElem = undefined;
      }

      // Determine which parent element to use as the container for rendering
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
            options.debug,
            `Parent element not found (#${overlayParentId}), creating and appending to body...`
          );
          // Create our own parent element and prepend to body
          parentElem = document.createElement("div");
          parentElem.id = overlayParentId;
          parentElem.className = "fides-overlay";
          document.body.prepend(parentElem);
        }
      }
      // update CSS variables based on configured primary color
      if (options.fidesPrimaryColor) {
        document.documentElement.style.setProperty(
          "--fides-overlay-primary-color",
          options.fidesPrimaryColor
        );
        const lighterPrimaryColor: string = generateLighterColor(
          options.fidesPrimaryColor,
          ColorFormat.HEX,
          1
        );
        document.documentElement.style.setProperty(
          "--fides-overlay-primary-button-background-hover-color",
          lighterPrimaryColor
        );
      }

      if (
        experience.experience_config?.component === ComponentType.MODAL ||
        experience.experience_config?.component ===
          ComponentType.BANNER_AND_MODAL ||
        experience.experience_config?.component === ComponentType.TCF_OVERLAY
      ) {
        // Render the Overlay to the DOM!
        renderOverlay(
          {
            options,
            experience,
            i18n,
            fidesRegionString,
            cookie,
            savedConsent,
          },
          parentElem
        );
        debugLog(options.debug, "Fides overlay is now in the DOM!");
        renderedParentElem = parentElem;
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
