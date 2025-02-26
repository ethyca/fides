import { ContainerNode, render } from "preact";

import { OverlayProps } from "../components/types";
import { ComponentType } from "./consent-types";
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
  propertyId,
  translationOverrides,
}: OverlayProps & {
  renderOverlay?: (props: OverlayProps, parent: ContainerNode) => void;
}): Promise<void> => {
  fidesDebugger("Initializing Fides consent overlays...");

  const renderFidesOverlay = async (): Promise<void> => {
    try {
      fidesDebugger("Injecting Fides overlay CSS & HTML into the DOM...");

      // If this function is called multiple times (e.g. due to calling
      // Fides.reinitialize() or similar), first ensure we unmount any
      // previously rendered instances
      if (renderedParentElem) {
        fidesDebugger(
          "Detected that Fides overlay was previously rendered! Unmounting previous instance from the DOM.",
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

      // update CSS variables based on configured primary color
      if (options.fidesPrimaryColor) {
        fidesDebugger("setting primary color to", options.fidesPrimaryColor);
        document.documentElement.style.setProperty(
          "--fides-overlay-primary-color",
          options.fidesPrimaryColor,
        );
        const lighterPrimaryColor: string = generateLighterColor(
          options.fidesPrimaryColor,
          ColorFormat.HEX,
          1,
        );
        document.documentElement.style.setProperty(
          "--fides-overlay-primary-button-background-hover-color",
          lighterPrimaryColor,
        );
      }

      // Determine which parent element to use as the container for rendering
      let parentElem;
      if (options.fidesEmbed) {
        parentElem = document.getElementById(FIDES_EMBED_CONTAINER_ID);
        if (!parentElem) {
          // wait until the hosting page's container element is available before proceeding in this script and attempting to render the embedded overlay. This is useful for dynamic (SPA) pages and pages that load the modal link element after the Fides script has loaded.
          fidesDebugger(
            `Embed container not found (#${FIDES_EMBED_CONTAINER_ID}), waiting for it to be added to the DOM...`,
          );
          const checkEmbedContainer = async () =>
            new Promise<void>((resolve) => {
              let attempts = 0;
              let interval = 200;
              const checkInterval = setInterval(() => {
                parentElem = document.getElementById(FIDES_EMBED_CONTAINER_ID);
                if (parentElem) {
                  clearInterval(checkInterval);
                  resolve();
                } else {
                  attempts += 1;
                  // if the container is not found after 5 attempts, increase the interval to reduce the polling frequency
                  if (attempts >= 5 && interval < 1000) {
                    interval += 200;
                  }
                }
              }, interval);
            });
          await checkEmbedContainer();
        }
      } else {
        // Find or create the parent element where we should insert the overlay
        const overlayParentId =
          options.overlayParentId || FIDES_OVERLAY_DEFAULT_ID;
        parentElem = document.getElementById(overlayParentId);
        if (!parentElem) {
          fidesDebugger(
            `Parent element not found (#${overlayParentId}), creating and appending to body...`,
          );
          // Create our own parent element and prepend to body
          parentElem = document.createElement("div");
          parentElem.id = overlayParentId;
          parentElem.className = "fides-overlay";
          document.body.prepend(parentElem);
        }
      }

      if (!parentElem) {
        return await Promise.reject(
          new Error("There was a problem rendering the Fides overlay."),
        );
      }

      if (
        !!renderOverlay &&
        (experience.experience_config?.component === ComponentType.MODAL ||
          experience.experience_config?.component ===
            ComponentType.BANNER_AND_MODAL ||
          experience.experience_config?.component === ComponentType.TCF_OVERLAY)
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
            propertyId,
            translationOverrides,
          },
          parentElem,
        );
        fidesDebugger("Fides overlay is now in the DOM!");
        renderedParentElem = parentElem;
      }
      return await Promise.resolve();
    } catch (e) {
      fidesDebugger(e);
      return Promise.reject(e);
    }
  };

  // Ensure we only render the overlay to the document once it's interactive
  // NOTE: do not wait for "complete" state, as this can delay rendering on sites with heavy assets
  if (document?.readyState === "loading") {
    fidesDebugger(
      "document readyState is not yet 'interactive', adding 'readystatechange' event listener and waiting...",
    );
    document.addEventListener("readystatechange", async () => {
      if (document.readyState === "interactive") {
        fidesDebugger("document fully loaded and parsed");
        renderFidesOverlay();
      }
    });
  } else {
    renderFidesOverlay();
  }
  return Promise.resolve();
};
