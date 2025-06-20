import { FidesEvent, FidesEventType } from "../docs";
import {
  ConsentFlagType,
  ConsentNonApplicableFlagMode,
  FidesGlobal,
  NoticeConsent,
} from "../lib/consent-types";
import { applyOverridesToConsent } from "../lib/consent-utils";
import { FidesEventDetail } from "../lib/events";

declare global {
  interface Window {
    dataLayer?: any[];
    Fides: FidesGlobal;
  }
}

/**
 * Defines the structure of the Fides variable pushed to the GTM data layer
 */
type FidesVariable = Omit<FidesEvent["detail"], "consent"> & {
  consent: NoticeConsent;
};

export interface GtmOptions {
  non_applicable_flag_mode?: ConsentNonApplicableFlagMode;
  flag_type?: ConsentFlagType;
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
  let consentValues: NoticeConsent = consent;
  const flagType =
    options?.flag_type ??
    window.Fides?.options?.fidesConsentFlagType ??
    ConsentFlagType.BOOLEAN;
  const nonApplicableFlagMode =
    options?.non_applicable_flag_mode ??
    window.Fides?.options?.fidesConsentNonApplicableFlagMode ??
    ConsentNonApplicableFlagMode.OMIT;

  const privacyNotices = window.Fides?.experience?.privacy_notices ?? [];
  const nonApplicablePrivacyNotices =
    window.Fides?.experience?.non_applicable_privacy_notices;

  consentValues = applyOverridesToConsent(
    consent,
    nonApplicablePrivacyNotices,
    privacyNotices,
    flagType,
    nonApplicableFlagMode,
  );

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
    FidesInitialized: true, // deprecated
    FidesConsentLoaded: true,
    FidesReady: true,
    FidesUpdating: true,
    FidesUpdated: true,
    FidesUIChanged: true,
    FidesUIShown: true,
    FidesModalClosed: true,
  };

  // If Fides was already initialized, publish a synthetic event immediately
  // Initialize this before setting up event listeners to ensure we check before FidesInitialized event potentially runs.
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

  const events = Object.entries(fidesEvents)
    .filter(([, dispatchToGtm]) => dispatchToGtm)
    .map(([key]) => key) as FidesEventType[];

  // Listen for Fides events and cross-publish them to GTM
  events.forEach((eventName) => {
    window.addEventListener(eventName, (event) =>
      pushFidesVariableToGTM(event, options),
    );
  });
};
