import { CmpApi, SignalStatus, TcfEuV2, TcfEuV2Field } from "@iabgpp/cmpapi";

import {
  ComponentType,
  ConsentMechanism,
  FidesCookie,
  NoticeConsent,
  PrivacyExperience,
  PrivacyExperienceMinimal,
} from "../consent-types";
import { DecodedFidesString, decodeFidesString } from "../fides-string";
import { areLocalesEqual } from "../i18n/i18n-utils";
import { updateConsent } from "../preferences";
import { EMPTY_ENABLED_IDS } from "../tcf/constants";
import { EnabledIds, TcfSavePreferences } from "../tcf/types";
import {
  createTcfSavePayload,
  createTcfSavePayloadFromMinExp,
  updateTCFCookie,
} from "../tcf/utils";
import { getGppSectionAndRegion } from "./gpp-utils";

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
  const { privacy_notices: notices = [] } = experience;

  const { gppRegion, gppSection } = getGppSectionAndRegion(
    experience.region,
    experience.gpp_settings?.us_approach,
    experience.privacy_notices,
  );

  if (!gppRegion || !gppSection) {
    fidesDebugger(
      "GPP: current state isn't supported, returning empty consent.",
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
 * 6. Calls updateConsent with the formatted consent preferences
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
  const { gpp: gppString }: DecodedFidesString = decodeFidesString(fidesString);
  if (!fidesString || !gppString || !cmpApi) {
    return;
  }

  const { locale } = window.Fides;
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

  if (!isTCF) {
    // Handle non-TCF case
    const consent: NoticeConsent = getConsentFromGppCmpApi({
      cmpApi,
      experience: experience as PrivacyExperience,
    });
    updateConsent(window.Fides, { noticeConsent: consent });
  } else {
    // Handle TCF case
    const enabledIds = getTcfPreferencesFromCmpApi({
      cmpApi,
      experience,
    });

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

    const noticeConsent: NoticeConsent = {};
    privacyNoticeItems.forEach((item) => {
      if (item.notice.consent_mechanism !== ConsentMechanism.NOTICE_ONLY) {
        noticeConsent[item.notice.notice_key] =
          enabledIds.purposesConsent.includes(item.notice.id);
      } else {
        noticeConsent[item.notice.notice_key] = true;
      }
    });
    updateConsent(window.Fides, {
      noticeConsent,
      tcf,
      updateCookie,
    });
  }
};
