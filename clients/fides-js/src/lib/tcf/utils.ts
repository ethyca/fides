import { TCString } from "@iabtechlabtcf/core";

import { extractIds } from "../common-utils";
import { getConsentContext } from "../consent-context";
import {
  ConsentMechanism,
  FidesCookie,
  PrivacyExperience,
  PrivacyExperienceMinimal,
  PrivacyNoticeWithPreference,
  RecordConsentServedRequest,
  SaveConsentPreference,
} from "../consent-types";
import { resolveConsentValue } from "../consent-value";
import {
  buildCookieConsentFromConsentPreferences,
  getFidesConsentCookie,
  transformTcfPreferencesToCookieKeys,
} from "../cookie";
import {
  transformConsentToFidesUserPreference,
  transformUserPreferenceToBoolean,
} from "../shared-consent-utils";
import { generateFidesString } from "../tcf";
import { FIDES_SYSTEM_COOKIE_KEY_MAP, TCF_KEY_MAP } from "./constants";
import { decodeFidesString, idsFromAcString } from "./fidesString";
import {
  EnabledIds,
  GVLTranslationJson,
  TCFFeatureRecord,
  TCFFeatureSave,
  TcfModels,
  TCFPurposeConsentRecord,
  TCFPurposeLegitimateInterestsRecord,
  TCFPurposeSave,
  TcfSavePreferences,
  TCFSpecialFeatureSave,
  TCFSpecialPurposeSave,
  TCFVendorConsentRecord,
  TCFVendorLegitimateInterestsRecord,
  TCFVendorSave,
} from "./types";

type TcfSave =
  | TCFPurposeSave
  | TCFSpecialPurposeSave
  | TCFFeatureSave
  | TCFSpecialFeatureSave
  | TCFVendorSave;

/**
 * Populates TCF entities with items from both cookie.tcf_consent and cookie.fides_string.
 * We must look at both because they contain non-overlapping info that is required for a complete TCFEntities object.
 * Returns TCF entities to be assigned to an experience.
 */
export const buildTcfEntitiesFromCookieAndFidesString = (
  experience: PrivacyExperience,
  cookie: FidesCookie,
) => {
  const tcfEntities = {
    tcf_purpose_consents: experience.tcf_purpose_consents,
    tcf_purpose_legitimate_interests:
      experience.tcf_purpose_legitimate_interests,
    tcf_special_purposes: experience.tcf_special_purposes,
    tcf_features: experience.tcf_features,
    tcf_special_features: experience.tcf_special_features,
    tcf_vendor_consents: experience.tcf_vendor_consents,
    tcf_vendor_legitimate_interests: experience.tcf_vendor_legitimate_interests,
    tcf_system_consents: experience.tcf_system_consents,
    tcf_system_legitimate_interests: experience.tcf_system_legitimate_interests,
  };

  // First update tcfEntities based on the `cookie.tcf_consent` obj
  FIDES_SYSTEM_COOKIE_KEY_MAP.forEach(({ cookieKey, experienceKey }) => {
    const cookieConsent = cookie.tcf_consent[cookieKey] ?? {};
    // @ts-ignore the array map should ensure we will get the right record type
    tcfEntities[experienceKey] = experience[experienceKey]?.map((item) => {
      // Object.keys converts keys to strings, so we coerce id to string here
      const preference = Object.keys(cookieConsent).includes(item.id as string)
        ? transformConsentToFidesUserPreference(
            Boolean(cookieConsent[item.id]),
            ConsentMechanism.OPT_IN,
          )
        : item.default_preference;
      return { ...item, current_preference: preference };
    });
  });
  // todo- consider custom notices too

  // Now update tcfEntities based on the fides string
  if (cookie.fides_string) {
    const { tc: tcString, ac: acString } = decodeFidesString(
      cookie.fides_string,
    );
    const acStringIds = idsFromAcString(acString);

    // Populate every field from tcModel
    const tcModel = TCString.decode(tcString);
    TCF_KEY_MAP.forEach(({ experienceKey, tcfModelKey }) => {
      const isVendorKey =
        tcfModelKey === "vendorConsents" ||
        tcfModelKey === "vendorLegitimateInterests";
      const tcIds = Array.from(tcModel[tcfModelKey])
        .filter(([, consented]) => consented)
        .map(([id]) => (isVendorKey ? `gvl.${id}` : id));
      // @ts-ignore the array map should ensure we will get the right record type
      tcfEntities[experienceKey] = experience[experienceKey]?.map((item) => {
        let consented = !!tcIds.find((id) => id === item.id);
        // Also check the AC string, which only applies to tcf_vendor_consents
        if (
          experienceKey === "tcf_vendor_consents" &&
          acStringIds.find((id) => id === item.id)
        ) {
          consented = true;
        }
        return {
          ...item,
          current_preference: transformConsentToFidesUserPreference(
            consented,
            ConsentMechanism.OPT_IN,
          ),
        };
      });
    });
  }

  return tcfEntities;
};

/**
 * TCF version of updating prefetched experience, based on:
 * 1) experience: pre-fetched or client-side experience-based consent configuration
 * 2) cookie: cookie containing user preference.

 *
 * Returns updated experience with user preferences. We have a separate function for notices
 * and for TCF so that the bundle trees do not overlap.
 */
export const updateExperienceFromCookieConsentTcf = ({
  experience,
  cookie,
  debug,
}: {
  experience: PrivacyExperience;
  cookie: FidesCookie;
  debug?: boolean;
}): PrivacyExperience => {
  // DEFER (PROD-1568) - instead of updating experience here, push this logic into UI
  const tcfEntities = buildTcfEntitiesFromCookieAndFidesString(
    experience,
    cookie,
  );

  if (debug) {
    fidesDebugger(
      `Returning updated pre-fetched experience with user consent.`,
      experience,
    );
  }
  return { ...experience, ...tcfEntities };
};

/**
 * Constructs the TCF notices served props based on the privacy experience.
 * If the experience is minimal, it will use the minimal TCF fields directly
 * which are already in the correct format.
 */
export const constructTCFNoticesServedProps = (
  privacyExperience: PrivacyExperience | PrivacyExperienceMinimal,
): Partial<RecordConsentServedRequest> => {
  if (!privacyExperience) {
    return {};
  }
  if (!privacyExperience.minimal_tcf) {
    const experience = privacyExperience as PrivacyExperience;
    return {
      tcf_purpose_consents: extractIds(experience.tcf_purpose_consents),
      tcf_purpose_legitimate_interests: extractIds(
        experience.tcf_purpose_legitimate_interests,
      ),
      tcf_special_purposes: extractIds(experience.tcf_special_purposes),
      tcf_vendor_consents: extractIds(experience.tcf_vendor_consents),
      tcf_vendor_legitimate_interests: extractIds(
        experience.tcf_vendor_legitimate_interests,
      ),
      tcf_features: extractIds(experience.tcf_features),
      tcf_special_features: extractIds(experience.tcf_special_features),
      tcf_system_consents: extractIds(experience.tcf_system_consents),
      tcf_system_legitimate_interests: extractIds(
        experience.tcf_system_legitimate_interests,
      ),
    };
  }

  const minExperience = privacyExperience as PrivacyExperienceMinimal;
  return {
    tcf_purpose_consents: minExperience.tcf_purpose_consent_ids ?? [],
    tcf_purpose_legitimate_interests:
      minExperience.tcf_purpose_legitimate_interest_ids ?? [],
    tcf_special_purposes: minExperience.tcf_special_purpose_ids ?? [],
    tcf_vendor_consents: minExperience.tcf_vendor_consent_ids ?? [],
    tcf_vendor_legitimate_interests:
      minExperience.tcf_vendor_legitimate_interest_ids ?? [],
    tcf_features: minExperience.tcf_feature_ids ?? [],
    tcf_special_features: minExperience.tcf_special_feature_ids ?? [],
    tcf_system_consents: minExperience.tcf_system_consent_ids ?? [],
    tcf_system_legitimate_interests:
      minExperience.tcf_system_legitimate_interest_ids ?? [],
  };
};

const resolveConsentValueFromTcfModel = (
  model:
    | TCFPurposeConsentRecord
    | TCFPurposeLegitimateInterestsRecord
    | TCFFeatureRecord
    | TCFVendorConsentRecord
    | TCFVendorLegitimateInterestsRecord,
) => {
  if (model.current_preference) {
    return transformUserPreferenceToBoolean(model.current_preference);
  }

  return transformUserPreferenceToBoolean(model.default_preference);
};

/**
 * Retrieves the enabled IDs from the given TcfModels list. This is used to
 * determine which IDs are currently enabled for the user to display in the UI.
 */
export const getEnabledIds = (modelList: TcfModels) => {
  if (!modelList) {
    return [];
  }
  return modelList
    .map((model) => {
      const value = resolveConsentValueFromTcfModel(model);
      return { ...model, consentValue: value };
    })
    .filter((model) => model.consentValue)
    .map((model) => `${model.id}`);
};

/**
 * Retrieves the enabled IDs from the given Notice list. This is used to
 * determine which IDs are currently enabled for the user to display in the UI.
 */
export const getEnabledIdsNotice = (
  noticeList: PrivacyNoticeWithPreference[],
) => {
  console.log("notice list:");
  console.log(noticeList);
  if (!noticeList) {
    return [];
  }
  const parsedCookie: FidesCookie | undefined = getFidesConsentCookie();
  const context = getConsentContext();
  console.log("consent context:");
  console.log(context);

  const result = noticeList
    .map((notice) => {
      const value = resolveConsentValue(notice, context, parsedCookie?.consent);
      return { ...notice, consentValue: value };
    })
    .filter((notice) => notice.consentValue)
    .map((notice) => `${notice.id}`);
  console.log("enabled ids notice:");
  console.log(result);
  return result;
};

const transformTcfModelToTcfSave = ({
  modelList,
  enabledIds,
}: {
  modelList: TcfModels;
  enabledIds: string[];
}): TcfSave[] | null => {
  if (!modelList) {
    return [];
  }
  return modelList.map((model) => {
    const preference = transformConsentToFidesUserPreference(
      enabledIds.includes(`${model.id}`),
    );
    return {
      id: model.id,
      preference,
    };
  }) as TcfSave[];
};

const transformTcfIdsToTcfSave = (enabledIds: string[]): TcfSave[] | null => {
  if (!enabledIds?.length) {
    return [];
  }
  return enabledIds.map((id) => {
    const preference = transformConsentToFidesUserPreference(true);
    let updatedId: string | number = id;
    if (!Number.isNaN(parseInt(id, 10))) {
      updatedId = parseInt(id, 10);
    }
    return {
      id: updatedId,
      preference,
    };
  }) as TcfSave[];
};

interface TcfSavePayloadProps<T> {
  experience: T;
  enabledIds: EnabledIds;
}

/**
 * Creates a TCF save payload based on the user's enabled IDs.
 */
export const createTcfSavePayload = ({
  experience,
  enabledIds,
}: TcfSavePayloadProps<PrivacyExperience>): TcfSavePreferences => {
  // Because systems were combined with vendors to make the UI easier to work with,
  // we need to separate them out now (the backend treats them as separate entities).
  const enabledConsentSystemIds: string[] = [];
  const enabledConsentVendorIds: string[] = [];
  const enabledLegintSystemIds: string[] = [];
  const enabledLegintVendorIds: string[] = [];
  enabledIds.vendorsConsent.forEach((id) => {
    if (experience.tcf_system_consents?.map((s) => s.id).includes(id)) {
      enabledConsentSystemIds.push(id);
    } else {
      enabledConsentVendorIds.push(id);
    }
  });
  enabledIds.vendorsLegint.forEach((id) => {
    if (
      experience.tcf_system_legitimate_interests?.map((s) => s.id).includes(id)
    ) {
      enabledLegintSystemIds.push(id);
    } else {
      enabledLegintVendorIds.push(id);
    }
  });

  return {
    purpose_consent_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_purpose_consents,
      enabledIds: enabledIds.purposesConsent,
    }) as TCFPurposeSave[],
    purpose_legitimate_interests_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_purpose_legitimate_interests,
      enabledIds: enabledIds.purposesLegint,
    }) as TCFPurposeSave[],
    special_feature_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_special_features,
      enabledIds: enabledIds.specialFeatures,
    }) as TCFSpecialFeatureSave[],
    vendor_consent_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_vendor_consents,
      enabledIds: enabledConsentVendorIds,
    }) as TCFVendorSave[],
    vendor_legitimate_interests_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_vendor_legitimate_interests,
      enabledIds: enabledLegintVendorIds,
    }) as TCFVendorSave[],
    system_consent_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_system_consents,
      enabledIds: enabledConsentSystemIds,
    }) as TCFVendorSave[],
    system_legitimate_interests_preferences: transformTcfModelToTcfSave({
      modelList: experience.tcf_system_legitimate_interests,
      enabledIds: enabledLegintSystemIds,
    }) as TCFVendorSave[],
  };
};

export const createTcfSavePayloadFromMinExp = ({
  experience,
  enabledIds,
}: TcfSavePayloadProps<PrivacyExperienceMinimal>) => {
  // Because systems were combined with vendors to make the UI easier to work with,
  // we need to separate them out now (the backend treats them as separate entities).
  const enabledConsentSystemIds: string[] = [];
  const enabledConsentVendorIds: string[] = [];
  const enabledLegintSystemIds: string[] = [];
  const enabledLegintVendorIds: string[] = [];
  enabledIds.vendorsConsent.forEach((id) => {
    if (experience.tcf_system_consent_ids?.includes(id)) {
      enabledConsentSystemIds.push(id);
    } else {
      enabledConsentVendorIds.push(id);
    }
  });
  enabledIds.vendorsLegint.forEach((id) => {
    if (experience.tcf_system_legitimate_interest_ids?.includes(id)) {
      enabledLegintSystemIds.push(id);
    } else {
      enabledLegintVendorIds.push(id);
    }
  });

  return {
    purpose_consent_preferences: transformTcfIdsToTcfSave(
      enabledIds.purposesConsent,
    ) as TCFPurposeSave[],
    purpose_legitimate_interests_preferences: transformTcfIdsToTcfSave(
      enabledIds.purposesLegint,
    ) as TCFPurposeSave[],
    special_feature_preferences: transformTcfIdsToTcfSave(
      enabledIds.specialFeatures,
    ) as TCFSpecialFeatureSave[],
    vendor_consent_preferences: transformTcfIdsToTcfSave(
      enabledConsentVendorIds,
    ) as TCFVendorSave[],
    vendor_legitimate_interests_preferences: transformTcfIdsToTcfSave(
      enabledLegintVendorIds,
    ) as TCFVendorSave[],
    system_consent_preferences: transformTcfIdsToTcfSave(
      enabledConsentSystemIds,
    ) as TCFVendorSave[],
    system_legitimate_interests_preferences: transformTcfIdsToTcfSave(
      enabledLegintSystemIds,
    ) as TCFVendorSave[],
  };
};

/**
 * Updates the Fides cookie with the provided data.
 *
 * `tcf` and `enabledIds` should represent the same data, where `tcf` is what is
 * sent to the backend, and `enabledIds` is what the FE uses. They have diverged
 * because the backend has not implemented separate vendor legint/consents yet.
 * Therefore, we need both entities right now, but eventually we should be able to
 * only use one. In other words, `enabledIds` has a field for `vendorsConsent` and
 * `vendorsLegint` but `tcf` only has `vendors`.
 *
 * @param oldCookie - The old Fides cookie.
 * @param tcf - The TCF save preferences representing the data sent to the backend.
 * @param enabledIds - The user's enabled IDs.
 * @param experience - The full privacy experience.
 * @param consentPreferencesToSave - Any Custom Notice preferences to save.
 * @returns A promise that resolves to the updated Fides cookie.
 */
export const updateCookie = async (
  oldCookie: FidesCookie,
  tcf: TcfSavePreferences,
  enabledIds: EnabledIds,
  experience: PrivacyExperience | PrivacyExperienceMinimal,
  consentPreferencesToSave: SaveConsentPreference[],
): Promise<FidesCookie> => {
  const tcString = await generateFidesString({
    tcStringPreferences: enabledIds,
    experience,
  });
  const result = {
    ...oldCookie,
    fides_string: tcString,
    tcf_consent: transformTcfPreferencesToCookieKeys(tcf),
    tcf_version_hash: experience.meta?.version_hash,
  };
  if (consentPreferencesToSave) {
    result.consent = buildCookieConsentFromConsentPreferences(
      consentPreferencesToSave,
    );
  }
  return result;
};

/**
 * Retrieves a combined list of GVL Purpose and Special Feature names
 * based on the provided GVL translations and locale for use in the
 * TCF banner. This list matches the names provided in the minimal TCF
 * experience. Changes here should be replicated in the /privacy-experience
 * endpoint for minimal_tcf and vice versa. The only difference is that
 * the /privacy-experience endpoint sends the purpose types as separate
 * arrays, while this function combines them into one. TCFOverlay.tsx combines
 * the minimal_tcf experience into one list in a similar way.
 */
export const getGVLPurposeList = (gvlTranslations: Record<string, any>) => {
  const purposeTypes = ["purposes", "specialFeatures"];
  const GVLPurposeList: string[] = [];
  purposeTypes.forEach((type) => {
    const purpose = gvlTranslations[type] as GVLTranslationJson["purposes"];
    Object.keys(purpose).forEach((key) => {
      GVLPurposeList.push(purpose[key].name.trim());
    });
  });
  return GVLPurposeList;
};
