import { CookieKeyConsent } from "../lib/cookie";
import { FidesEventDetail } from "../lib/events";

declare global {
  interface Window {
    dataLayer?: any[];
  }
}

/**
 * Defines the structure of the Fides variable pushed to the GTM data layer
 */
interface FidesVariable {
  consent: CookieKeyConsent;
}

// Helper function to push the Fides variable to the GTM data layer from a FidesEvent
const pushFidesVariableToGTM = (fidesEvent: {
  type: string;
  detail: FidesEventDetail;
}) => {
  // Initialize the dataLayer object, just in case we run before GTM is initialized
  const dataLayer = window.dataLayer ?? [];
  window.dataLayer = dataLayer;

  // Construct the Fides variable that will be pushed to GTM
  const Fides: FidesVariable = {
    consent: fidesEvent.detail.consent,
  };

  // Push to the GTM dataLayer
  if (fidesEvent.type === "FidesInitialized") {
    // NOTE: For backwards-compatibility, we don't provide an "event" for the
    // initialization event, just for updates.
    // TODO: check if adding the "event" to the existing behaviour would be a breaking change... probably not?
    dataLayer.push({ Fides });
  } else {
    dataLayer.push({ event: fidesEvent.type, Fides });
  }
};

/**
 * Call Fides.gtm() to configure the Fides <> Google Tag Manager integration.
 * The user's consent choices will automatically be pushed into GTM's
 * `dataLayer` under `Fides.consent` variable.
 */
export const gtm = () => {
  // Listen for Fides events and cross-publish them to GTM
  window.addEventListener("FidesInitialized", (event) =>
    pushFidesVariableToGTM(event)
  );
  window.addEventListener("FidesUpdated", (event) =>
    pushFidesVariableToGTM(event)
  );

  // If Fides was already initialized, publish a synthetic event immediately
  if (window.Fides.initialized) {
    pushFidesVariableToGTM({
      type: "FidesInitialized",
      detail: { consent: window.Fides.consent },
    });
  }
};
