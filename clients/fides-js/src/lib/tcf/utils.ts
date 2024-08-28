import { TCString } from "@iabtechlabtcf/core";

import {
  ConsentMechanism,
  FidesCookie,
  PrivacyExperience,
} from "../consent-types";
import { debugLog } from "../consent-utils";
import { transformConsentToFidesUserPreference } from "../shared-consent-utils";
import { FIDES_SYSTEM_COOKIE_KEY_MAP, TCF_KEY_MAP } from "./constants";
import { decodeFidesString, idsFromAcString } from "./fidesString";

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
    debugLog(
      debug,
      `Returning updated pre-fetched experience with user consent.`,
      experience,
    );
  }
  return { ...experience, ...tcfEntities };
};
