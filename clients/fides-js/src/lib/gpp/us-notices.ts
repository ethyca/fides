/**
 * Helper functions to set the GPP CMP API based on Fides values
 */

import { CmpApi, UsNatField } from "@iabgpp/cmpapi";

import { FidesCookie, PrivacyExperience } from "../consent-types";
import { FIDES_US_REGION_TO_GPP_SECTION } from "./constants";
import { GPPSection, GPPSettings, GPPUSApproach } from "./types";

const US_NATIONAL_REGION = "us";

const setMspaSections = ({
  cmpApi,
  sectionName,
  gppSettings,
}: {
  cmpApi: CmpApi;
  sectionName: string;
  gppSettings: GPPSettings | undefined;
}) => {
  if (!gppSettings) {
    return;
  }

  const mspaFields = [
    {
      gppSettingField: gppSettings.mspa_covered_transactions,
      cmpApiField: UsNatField.MSPA_COVERED_TRANSACTION,
    },
    {
      gppSettingField: gppSettings.mspa_opt_out_option_mode,
      cmpApiField: UsNatField.MSPA_OPT_OUT_OPTION_MODE,
    },
    {
      gppSettingField: gppSettings.mspa_service_provider_mode,
      cmpApiField: UsNatField.MSPA_SERVICE_PROVIDER_MODE,
    },
  ];
  mspaFields.forEach(({ gppSettingField, cmpApiField }) => {
    cmpApi.setFieldValue(sectionName, cmpApiField, gppSettingField ? 1 : 2);
  });
};

/**
 * Checks if a given region is in the US based on the provided region string's prefix.
 * Also returns true if the region is the US_NATIONAL_REGION.
 */
const isUsRegion = (region: string) => region?.toLowerCase().startsWith("us");

/**
 * For US National, the privacy experience region is still the state where the user came from.
 * However, the GPP field mapping will only contain "us", so make sure we use "us" (US_NATIONAL_REGION) when we are configured for the national case.
 * Otherwise, we can use the experience region directly.
 */
const deriveGppFieldRegion = ({
  experienceRegion,
  usApproach,
}: {
  experienceRegion: string;
  usApproach: GPPUSApproach | undefined;
}) => {
  if (isUsRegion(experienceRegion) && usApproach === GPPUSApproach.NATIONAL) {
    return US_NATIONAL_REGION;
  }
  return experienceRegion;
};

/**
 * Sets the appropriate fields on a GPP CMP API model for whether notices were provided
 *
 * Returns GPP section IDs which were updated
 */
export const setGppNoticesProvidedFromExperience = ({
  cmpApi,
  experience,
}: {
  cmpApi: CmpApi;
  experience: PrivacyExperience;
}) => {
  const sectionsChanged = new Set<GPPSection>();
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
    // if we're using the "all" approach, and the user's state isn't supported yet, we should default to national.
    gppRegion = US_NATIONAL_REGION;
    gppSection = FIDES_US_REGION_TO_GPP_SECTION[gppRegion];
  }

  if (
    !gppSection ||
    (gppRegion === US_NATIONAL_REGION && usApproach === GPPUSApproach.STATE)
  ) {
    // If we don't have a section, we can't set anything.
    // If we're using the state approach we shouldn't return the national section, even if region is set to national.
    return [];
  }

  sectionsChanged.add(gppSection);

  notices.forEach((notice) => {
    const { gpp_field_mapping: fieldMapping } = notice;
    const gppNotices = fieldMapping?.find(
      (fm) => fm.region === gppRegion,
    )?.notice;
    if (gppNotices) {
      gppNotices.forEach((gppNotice) => {
        // 1 means notice was provided
        cmpApi.setFieldValue(gppSection.name, gppNotice, 1);
      });
    }
  });

  // Set MSPA
  setMspaSections({ cmpApi, sectionName: gppSection.name, gppSettings });

  return Array.from(sectionsChanged);
};

/**
 * Sets the appropriate fields on a GPP CMP API model for user opt-outs
 *
 * Returns GPP sections which were updated
 */
export const setGppOptOutsFromCookieAndExperience = ({
  cmpApi,
  cookie,
  experience,
}: {
  cmpApi: CmpApi;
  cookie: FidesCookie;
  experience: PrivacyExperience;
}) => {
  const sectionsChanged = new Set<GPPSection>();
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
    // if we're using the all approach, and the current state isn't supported, we should default to national
    gppRegion = US_NATIONAL_REGION;
    gppSection = FIDES_US_REGION_TO_GPP_SECTION[gppRegion];
  }

  if (
    !gppSection ||
    (gppRegion === US_NATIONAL_REGION && usApproach === GPPUSApproach.STATE)
  ) {
    // If we don't have a section, we can't set anything.
    // If we're using the state approach, we shouldn't return the national section, even if region is set to national.
    return [];
  }

  sectionsChanged.add(gppSection);

  const { consent } = cookie;
  const noticeKeys = Object.keys(consent);
  noticeKeys.forEach((noticeKey) => {
    const privacyNotice = notices?.find((n) => n.notice_key === noticeKey);
    const consentValue = consent[noticeKey];
    if (privacyNotice) {
      const { gpp_field_mapping: fieldMapping } = privacyNotice;
      const gppMechanisms = fieldMapping?.find(
        (fm) => fm.region === gppRegion,
      )?.mechanism;
      if (gppMechanisms) {
        gppMechanisms.forEach((gppMechanism) => {
          // In general, 0 = N/A, 1 = Opted out, 2 = Did not opt out
          let value: string | string[] = gppMechanism.not_available; // if consentValue is undefined, we'll mark as N/A
          if (consentValue === false) {
            value = gppMechanism.opt_out;
          } else if (consentValue) {
            value = gppMechanism.not_opt_out;
          }
          let valueAsNum: number | number[] = +value;
          if (value.length > 1) {
            // If we have more than one bit, we should set it as an array, i.e. 111 should be [1,1,1]
            valueAsNum = value.split("").map((v) => +v);
          }
          cmpApi.setFieldValue(gppSection.name, gppMechanism.field, valueAsNum);
        });
      }
    }
  });

  setMspaSections({
    cmpApi,
    sectionName: gppSection.name,
    gppSettings,
  });

  return Array.from(sectionsChanged);
};
