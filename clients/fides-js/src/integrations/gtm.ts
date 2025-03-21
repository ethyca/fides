import { FidesEvent, FidesEventType } from "../docs";
import { FidesEventDetail } from "../lib/events";
import { transformConsentToFidesUserPreference } from "../lib/shared-consent-utils";

declare global {
  interface Window {
    dataLayer?: any[];
  }
}

/**
 * Defines the structure of the Fides variable pushed to the GTM data layer
 */
type FidesVariable = Omit<FidesEvent["detail"], "consent"> & {
  consent: Record<string, boolean | string>;
};

export interface GtmOptions {
  includeNotApplicable?: boolean;
  asStringValues?: boolean;
}

// Helper function to push the Fides variable to the GTM data layer from a FidesEvent
const pushFidesVariableToGTM = (
  fidesEvent: {
    type: string;
    detail: FidesEventDetail;
  },
  options?: GtmOptions,
) => {
  // Initialize the dataLayer object, just in case we run before GTM is initialized
  const dataLayer = window.dataLayer ?? [];
  window.dataLayer = dataLayer;
  const { detail, type } = fidesEvent;
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { consent, extraDetails, fides_string, timestamp } = detail;
  const { includeNotApplicable, asStringValues } = options ?? {};
  const consentValues: FidesVariable["consent"] = JSON.parse(
    JSON.stringify(consent),
  );
  const privacyNotices = window.Fides?.experience?.privacy_notices;
  const nonApplicablePrivacyNotices =
    window.Fides?.experience?.non_applicable_privacy_notices;

  if (privacyNotices && asStringValues) {
    Object.entries(consent).forEach(([key, value]) => {
      consentValues[key] = transformConsentToFidesUserPreference(
        value,
        privacyNotices.find((notice) => notice.notice_key === key)
          ?.consent_mechanism,
      );
    });
  }

  if (includeNotApplicable && nonApplicablePrivacyNotices) {
    nonApplicablePrivacyNotices.forEach((key) => {
      consentValues[key] = asStringValues ? "not_applicable" : true;
    });
  }

  // Construct the Fides variable that will be pushed to GTM
  const Fides: FidesVariable = {
    consent: consentValues,
    extraDetails,
    fides_string,
    timestamp,
  };

  // Push to the GTM dataLayer
  dataLayer.push({ event: type, Fides });
};

/**
 * Call Fides.gtm() to configure the Fides <> Google Tag Manager integration.
 * The user's consent choices will automatically be pushed into GTM's
 * `dataLayer` under `Fides.consent` variable.
 */
export const gtm = (options?: GtmOptions) => {
  // List every FidesEventType as a record so that new additional events are
  // considered by future developers as to whether they should be pushed to GTM.
  const fidesEvents: Record<FidesEventType, boolean> = {
    FidesInitializing: false,
    FidesInitialized: true,
    FidesUpdating: true,
    FidesUpdated: true,
    FidesUIChanged: true,
    FidesUIShown: true,
    FidesModalClosed: true,
  };

  const events = Object.entries(fidesEvents)
    .filter(([, dispatchToGtm]) => dispatchToGtm)
    .map(([key]) => key) as FidesEventType[];

  // Listen for Fides events and cross-publish them to GTM
  events.forEach((eventName) => {
    window.addEventListener(eventName, (event) =>
      pushFidesVariableToGTM(event, options),
    );
  });

  // If Fides was already initialized, publish a synthetic event immediately
  if (window.Fides?.initialized) {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const { consent, fides_meta, identity, tcf_consent } = window.Fides;
    // Lookup the timestamp of the original FidesInitialized performance mark
    const timestamp =
      performance?.getEntriesByName("FidesInitialized")[0]?.startTime;
    pushFidesVariableToGTM(
      {
        type: "FidesInitialized",
        detail: {
          consent,
          fides_meta,
          identity,
          tcf_consent,
          timestamp,
          extraDetails: {
            consentMethod: fides_meta?.consentMethod,
          },
        },
      },
      options,
    );
  }
};
