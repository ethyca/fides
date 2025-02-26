import { FidesEvent } from "../docs";
import { FidesEventDetail } from "../lib/events";

declare global {
  interface Window {
    dataLayer?: any[];
  }
}

/**
 * Defines the structure of the Fides variable pushed to the GTM data layer
 */
type FidesVariable = FidesEvent["detail"];

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
    extraDetails: fidesEvent.detail.extraDetails,
    fides_string: fidesEvent.detail.fides_string,
  };

  // Push to the GTM dataLayer
  dataLayer.push({ event: fidesEvent.type, Fides });
};

/**
 * Call Fides.gtm() to configure the Fides <> Google Tag Manager integration.
 * The user's consent choices will automatically be pushed into GTM's
 * `dataLayer` under `Fides.consent` variable.
 */
export const gtm = () => {
  // Listen for Fides events and cross-publish them to GTM
  window.addEventListener("FidesInitialized", (event) =>
    pushFidesVariableToGTM(event),
  );
  window.addEventListener("FidesUpdating", (event) =>
    pushFidesVariableToGTM(event),
  );
  window.addEventListener("FidesUpdated", (event) =>
    pushFidesVariableToGTM(event),
  );

  // If Fides was already initialized, publish a synthetic event immediately
  if (window.Fides?.initialized) {
    pushFidesVariableToGTM({
      type: "FidesInitialized",
      detail: {
        consent: window.Fides.consent,
        fides_meta: window.Fides.fides_meta,
        identity: window.Fides.identity,
        tcf_consent: window.Fides.tcf_consent,
        extraDetails: {
          consentMethod: window.Fides.fides_meta?.consentMethod,
        },
      },
    });
  }
};
