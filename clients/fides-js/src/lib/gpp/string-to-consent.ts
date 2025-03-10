import { CmpApi, SignalStatus, TcfEuV2, TcfEuV2Field } from "@iabgpp/cmpapi";

import {
  ComponentType,
  ConsentMethod,
  FidesCookie,
  NoticeConsent,
  PrivacyExperience,
  PrivacyExperienceMinimal,
  SaveConsentPreference,
} from "../consent-types";
import {
  constructFidesRegionString,
  createConsentPreferencesToSave,
} from "../consent-utils";
import { DecodedFidesString, decodeFidesString } from "../fidesString";
import { areLocalesEqual } from "../i18n/i18n-utils";
import { updateConsentPreferences } from "../preferences";
import { EMPTY_ENABLED_IDS } from "../tcf/constants";
import { EnabledIds, TcfSavePreferences } from "../tcf/types";
import {
  createTCFConsentPreferencesToSave,
  createTcfSavePayload,
  createTcfSavePayloadFromMinExp,
  updateTCFCookie,
} from "../tcf/utils";
import { FIDES_US_REGION_TO_GPP_SECTION } from "./constants";
import { GPPUSApproach } from "./types";
import { deriveGppFieldRegion, US_NATIONAL_REGION } from "./us-notices";

const FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS = [1, 3, 4, 5, 6];

/**
 * Gets the consent object from a GPP CMP API model based on the experience configuration
 *
 * This is the inverse of setGppOptOutsFromCookieAndExperience
 */
const getConsentFromGppCmpApi = ({
  cmpApi,
  experience,
}: {
  cmpApi: CmpApi;
  experience: PrivacyExperience;
}): NoticeConsent => {
  const consent: NoticeConsent = {};
  const {
    privacy_notices: notices = [],
    region: experienceRegion,
    gpp_settings: gppSettings,
  } = experience;
  const usApproach = gppSettings?.us_approach;
  let gppRegion = deriveGppFieldRegion({
    experienceRegion,
    usApproach,
  });
  let gppSection = FIDES_US_REGION_TO_GPP_SECTION[gppRegion];

  if (!gppSection && usApproach === GPPUSApproach.ALL) {
    fidesDebugger(
      'GPP: current state isn\'t supported, defaulting to USNat since "Both/All" approach is selected',
    );
    gppRegion = US_NATIONAL_REGION;
    gppSection = FIDES_US_REGION_TO_GPP_SECTION[gppRegion];
  }

  if (
    !gppSection ||
    (gppRegion === US_NATIONAL_REGION && usApproach === GPPUSApproach.STATE)
  ) {
    fidesDebugger(
      'GPP: current state isn\'t supported, returning empty consent since "US State" approach is selected',
    );
    return consent;
  }

  notices.forEach((notice) => {
    const { notice_key: noticeKey, gpp_field_mapping: fieldMapping } = notice;
    const gppMechanisms = fieldMapping?.find(
      (fm) => fm.region === gppRegion,
    )?.mechanism;

    if (gppMechanisms) {
      // For each mechanism, check the field value and determine the consent value
      const hasOptOut = gppMechanisms.some((gppMechanism) => {
        const fieldValue = cmpApi.getFieldValue(
          gppSection.name,
          gppMechanism.field,
        );

        // Convert field value to string for comparison
        const valueStr = Array.isArray(fieldValue)
          ? fieldValue.join("")
          : String(fieldValue);

        // Check if the value matches any of the defined states
        if (valueStr === gppMechanism.opt_out) {
          return true; // User has opted out
        }
        if (valueStr === gppMechanism.not_opt_out) {
          return false; // User has not opted out
        }
        // If value matches not_available or is undefined, we'll skip this mechanism
        return false;
      });

      if (hasOptOut !== undefined) {
        consent[noticeKey] = !hasOptOut; // Invert because true means consented (not opted out)
      }
    }
  });

  return consent;
};

/**
 * Gets the TCF preferences from a CMP API model based on the experience configuration
 */
const getTcfPreferencesFromCmpApi = ({
  cmpApi,
  experience,
}: {
  cmpApi: CmpApi;
  experience: PrivacyExperience | PrivacyExperienceMinimal;
}): EnabledIds => {
  const preferences: EnabledIds = EMPTY_ENABLED_IDS;

  const tcfeuv2 = cmpApi.getSection(TcfEuV2.NAME) as Record<
    TcfEuV2Field,
    unknown
  >;
  if (!tcfeuv2) {
    return preferences;
  }

  // Convert purpose consents - get indices where value is true
  const purposeConsents = (tcfeuv2.PurposeConsents as boolean[])
    .map((value, index) => (value ? (index + 1).toString() : null))
    .filter((value): value is string => value !== null);

  // Convert legitimate interests - get indices where value is true
  const purposeLegint = (tcfeuv2.PurposeLegitimateInterests as boolean[])
    .map((value, index) => (value ? (index + 1).toString() : null))
    .filter((value): value is string => value !== null);

  // Convert vendor consents and legitimate interests by adding "gvl." prefix
  const vendorConsents = (tcfeuv2.VendorConsents as number[]).map(
    (id) => `gvl.${id}`,
  );

  const vendorLegint = (tcfeuv2.VendorLegitimateInterests as number[]).map(
    (id) => `gvl.${id}`,
  );

  // Update preferences object
  preferences.purposesConsent = purposeConsents;
  preferences.purposesLegint = purposeLegint.filter(
    (id) =>
      !FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS.includes(parseInt(id, 10)),
  );
  preferences.vendorsConsent = vendorConsents;
  preferences.vendorsLegint = vendorLegint;

  // Convert special features from boolean array to string array of indices
  preferences.specialFeatures = (tcfeuv2.SpecialFeatureOptins as boolean[])
    .map((value, index) => (value ? (index + 1).toString() : null))
    .filter((value): value is string => value !== null);

  // Get special purposes and features from experience config
  if ("tcf_special_purposes" in experience) {
    preferences.specialPurposes =
      experience.tcf_special_purposes?.map((p) => p.id.toString()) || [];
    preferences.features =
      experience.tcf_features?.map((f) => f.id.toString()) || [];
  } else if ("tcf_special_purpose_ids" in experience) {
    preferences.specialPurposes =
      experience.tcf_special_purpose_ids?.map((id) => id.toString()) || [];
    preferences.features =
      experience.tcf_feature_ids?.map((id) => id.toString()) || [];
  }

  // Custom purposes consent remain empty as per example
  preferences.customPurposesConsent = [];

  return preferences;
};

interface FidesStringToConsentArgs {
  fidesString: string;
  cmpApi: CmpApi;
}

/**
 * Converts a Fides string to consent preferences and updates the CMP API
 *
 * This function handles both TCF and non-TCF consent scenarios:
 * 1. Decodes the provided Fides string and extracts GPP data
 * 2. Updates the CMP API with the GPP string and sets signal status
 * 3. Maps privacy notices with their translation ID
 * 4. Decodes consent preferences from appropriate CMP API
 * 5. Formats consent preferences to save
 * 6. Calls updateConsentPreferences with the formatted consent preferences
 *
 * @param {FidesStringToConsentArgs} args - The arguments object
 * @param {string} args.fidesString - The encoded Fides consent string containing GPP data
 * @param {CmpApi} args.cmpApi - The GPP CMP API instance to update with consent data
 * @returns {void}
 */
export const fidesStringToConsent = ({
  fidesString,
  cmpApi,
}: FidesStringToConsentArgs) => {
  if (!fidesString || !cmpApi) {
    return;
  }

  const { options, cookie, geolocation, locale, config } = window.Fides;
  const experience = window.Fides.experience as
    | PrivacyExperience
    | PrivacyExperienceMinimal;
  if (
    !experience ||
    !experience.experience_config ||
    !experience.privacy_notices
  ) {
    return;
  }

  const isTCF =
    experience.experience_config.component === ComponentType.TCF_OVERLAY;

  const { gpp: gppString }: DecodedFidesString = decodeFidesString(fidesString);
  const fidesRegionString = constructFidesRegionString(geolocation);
  const matchTranslation = experience.experience_config.translations.find((t) =>
    areLocalesEqual(t.language, locale),
  );

  if (!matchTranslation) {
    return;
  }

  // Set up GPP string
  cmpApi.setGppString(gppString);
  cmpApi.setSignalStatus(SignalStatus.READY);
  fidesDebugger("GPP: updated GPP from fides_string override", fidesString);

  // Map privacy notices with translations
  const privacyNoticeItems = experience.privacy_notices.map((notice) => ({
    notice,
    bestTranslation:
      notice.translations.find((t) => areLocalesEqual(t.language, locale)) ||
      null,
  }));

  let updateCookie: (oldCookie: FidesCookie) => Promise<FidesCookie>;
  let tcf: TcfSavePreferences | undefined;
  let consentPreferencesToSave: SaveConsentPreference[];

  if (!isTCF) {
    // Handle non-TCF case
    const consent: NoticeConsent = getConsentFromGppCmpApi({
      cmpApi,
      experience: experience as PrivacyExperience,
    });

    const enabledPrivacyNoticeKeys: string[] = Object.entries(consent)
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      .filter(([_, value]) => value)
      .map(([key]) => key);

    consentPreferencesToSave = createConsentPreferencesToSave(
      privacyNoticeItems,
      enabledPrivacyNoticeKeys,
    );

    fidesDebugger(
      "GPP: updating consent preferences based on fides_string override",
      consent,
    );
    updateCookie = (oldCookie) => Promise.resolve({ ...oldCookie, consent });
  } else {
    // Handle TCF case
    const enabledIds = getTcfPreferencesFromCmpApi({
      cmpApi,
      experience,
    });

    consentPreferencesToSave = createTCFConsentPreferencesToSave(
      privacyNoticeItems.map(({ notice, bestTranslation }) => ({
        ...notice,
        bestTranslation,
      })),
      enabledIds.customPurposesConsent,
    );

    tcf = experience.minimal_tcf
      ? createTcfSavePayloadFromMinExp({
          experience: experience as PrivacyExperienceMinimal,
          enabledIds,
        })
      : createTcfSavePayload({
          experience: experience as PrivacyExperience,
          enabledIds,
        });

    updateCookie = (oldCookie) =>
      updateTCFCookie(
        oldCookie,
        tcf as TcfSavePreferences,
        enabledIds,
        experience,
      );
  }

  // Update preferences with common parameters
  updateConsentPreferences({
    consentPreferencesToSave,
    privacyExperienceConfigHistoryId:
      matchTranslation.privacy_experience_config_history_id,
    experience,
    consentMethod: ConsentMethod.SCRIPT,
    options,
    userLocationString: fidesRegionString || undefined,
    cookie: cookie as FidesCookie,
    propertyId: config?.propertyId,
    tcf,
    updateCookie,
  });
};
