import { FidesEvent, FidesEventType } from "../docs";
import { FidesGlobal, UserConsentPreference } from "../lib/consent-types";
import { FidesEventDetail } from "../lib/events";
import { normalizeConsentValues } from "../lib/shared-consent-utils";

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
  consent: Record<string, boolean | string>;
};

export enum ConsentNonApplicableFlagMode {
  OMIT = "omit",
  INCLUDE = "include",
}

export enum ConsentFlagType {
  BOOLEAN = "boolean",
  CONSENT_MECHANISM = "consent_mechanism",
}

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

  // Get options from either the provided options or the Fides config, with
  // provided options taking precedence
  const overrideOptions = window.Fides?.options;
  const {
    non_applicable_flag_mode:
      nonApplicableFlagMode = overrideOptions?.fidesConsentNonApplicableFlagMode ??
        ConsentNonApplicableFlagMode.OMIT,
    flag_type: flagType = overrideOptions?.fidesConsentFlagType ??
      ConsentFlagType.BOOLEAN,
  } = options ?? {};

  const consentValues: FidesVariable["consent"] = {};
  const privacyNotices = window.Fides?.experience?.privacy_notices ?? [];
  const nonApplicablePrivacyNotices =
    window.Fides?.experience?.non_applicable_privacy_notices;

  // First set defaults for non-applicable privacy notices if needed
  if (
    nonApplicableFlagMode === ConsentNonApplicableFlagMode.INCLUDE &&
    nonApplicablePrivacyNotices
  ) {
    nonApplicablePrivacyNotices.forEach((key) => {
      consentValues[key] =
        flagType === ConsentFlagType.CONSENT_MECHANISM
          ? UserConsentPreference.NOT_APPLICABLE
          : true;
    });
  }

  // Then override with actual consent values
  if (consent) {
    const consentMechanisms = privacyNotices.reduce(
      (acc, notice) => ({
        ...acc,
        [notice.notice_key]: notice.consent_mechanism,
      }),
      {},
    );

    Object.assign(
      consentValues,
      normalizeConsentValues({
        consent,
        consentMechanisms,
        flagType,
      }),
    );
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
