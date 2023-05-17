import {FIDES_MODAL_LINK} from "~/lib/consent-types";
import {debugLog} from "~/lib/consent-utils";

/**
 * Hide pre-existing link in the DOM if we do not need to trigger a modal
 */
export const hideModalLink = (debug: boolean): void => {
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
export const bindModalLinkToModal = (debug: boolean): void => {
    // TODO- it's possible that this element does not exist by the time this method runs
    const modalLinkEl: HTMLElement | null =
        document.getElementById(FIDES_MODAL_LINK);
    if (
        modalLinkEl
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