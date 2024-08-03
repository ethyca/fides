import { ContainerNode, render } from "preact";

import { OverlayProps } from "../components/types";
import { fetchGvlTranslations } from "../services/api";
import { ComponentType } from "./consent-types";
import { debugLog } from "./consent-utils";
import { DEFAULT_LOCALE } from "./i18n";
import { loadMessagesFromGVLTranslations } from "./i18n/i18n-utils";
import { LOCALE_LANGUAGE_MAP } from "./i18n/locales";
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
}: OverlayProps & {
  renderOverlay: (props: OverlayProps, parent: ContainerNode) => void;
}): Promise<void> => {
  debugLog(options.debug, "Initializing Fides consent overlays...");

  if (experience.experience_config?.component === ComponentType.TCF_OVERLAY) {
    let gvlTranslations = await fetchGvlTranslations(
      options.fidesApiUrl,
      [i18n.locale],
      options.debug,
    );
    if (
      (!gvlTranslations || Object.keys(gvlTranslations).length === 0) &&
      experience.gvl
    ) {
      // if translations API fails or is empty, use the GVL object directly
      // as a fallback, since it already contains the english version of strings
      gvlTranslations = {};
      gvlTranslations[DEFAULT_LOCALE] = experience.gvl;
      // eslint-disable-next-line no-param-reassign
      experience.available_locales = [DEFAULT_LOCALE];
      i18n.setAvailableLanguages(
        LOCALE_LANGUAGE_MAP.filter((lang) => lang.locale === DEFAULT_LOCALE),
      );
      i18n.activate(DEFAULT_LOCALE);
    }
    loadMessagesFromGVLTranslations(
      i18n,
      gvlTranslations,
      experience.available_locales || [DEFAULT_LOCALE],
    );
  }

  async function renderFidesOverlay(): Promise<void> {
    try {
      debugLog(
        options.debug,
        "Rendering Fides overlay CSS & HTML into the DOM...",
      );

      // If this function is called multiple times (e.g. due to calling
      // Fides.reinitialize() or similar), first ensure we unmount any
      // previously rendered instances
      if (renderedParentElem) {
        debugLog(
          options.debug,
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
          debugLog(
            options.debug,
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
          debugLog(
            options.debug,
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
            propertyId,
          },
          parentElem,
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

  // Ensure we only render the overlay to the document once it's interactive
  // NOTE: do not wait for "complete" state, as this can delay rendering on sites with heavy assets
  if (document?.readyState === "loading") {
    debugLog(
      options.debug,
      "document readyState is not yet 'interactive', adding 'readystatechange' event listener and waiting...",
    );
    document.addEventListener("readystatechange", async () => {
      if (document.readyState === "interactive") {
        debugLog(options.debug, "document fully loaded and parsed");
        renderFidesOverlay();
      }
    });
  } else {
    renderFidesOverlay();
  }
  return Promise.resolve();
};
