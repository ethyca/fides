import {FIDES_MODAL_LINK} from "./consent-types";
import {debugLog} from "./consent-utils";

/**
 * Update to show the pre-existing modal link in the DOM to trigger the modal
 */
export const showModalLinkAndSetOnClick = (debug: boolean): void => {
    const modalLinkEl: HTMLElement | null =
        document.getElementById(FIDES_MODAL_LINK);
    if (
        modalLinkEl
    ) {
        debugLog(
            debug,
            `Fides modal link element found, updating to show it and set click event to trigger modal`
        );
        modalLinkEl.onclick = () => {
            // TODO: render modal component
        };
        modalLinkEl.style.display = "inline"
    } else {
        debugLog(
            debug,
            `Fides modal link element could not be found`
        );
    }
};