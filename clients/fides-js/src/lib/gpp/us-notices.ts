/**
 * Helper functions to set the GPP CMP API based on Fides values
 *
 * NOTE: Changes to this file should likely also be made in the
 * GPP encoder API implementation in `fidesplus`.
 */

import { CmpApi, UsNatField } from "@iabgpp/cmpapi";

import { FidesCookie, PrivacyExperience } from "../consent-types";
import { FIDES_US_REGION_TO_GPP_SECTION } from "./constants";
import { GPPSection, GPPSettings, GPPUSApproach } from "./types";

export const US_NATIONAL_REGION = "us";

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
      gppSettingField:
        gppSettings.mspa_covered_transactions &&
        gppSettings.mspa_opt_out_option_mode,
      cmpApiField: UsNatField.MSPA_OPT_OUT_OPTION_MODE,
    },
    {
      gppSettingField:
        gppSettings.mspa_covered_transactions &&
        gppSettings.mspa_service_provider_mode,
      cmpApiField: UsNatField.MSPA_SERVICE_PROVIDER_MODE,
    },
  ];

  mspaFields.forEach(({ gppSettingField, cmpApiField }) => {
    const isCoveredTransactions =
      cmpApiField === UsNatField.MSPA_COVERED_TRANSACTION;
    let value = 2; // Default to No

    if (!gppSettings.mspa_covered_transactions && !isCoveredTransactions) {
      value = 0; // When covered transactions is false, other fields should be disabled
    } else if (gppSettingField) {
      value = 1; // Yes
    }

    cmpApi.setFieldValue(sectionName, cmpApiField, value);
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
export const deriveGppFieldRegion = ({
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

type CmpApiUpdater = (props: {
  cmpApi: CmpApi;
  gppRegion: string;
  gppSection: GPPSection;
  experience: PrivacyExperience;
  cookie?: FidesCookie;
}) => void;

export const getGppSectionAndRegion = (
  experience: PrivacyExperience,
): { gppRegion?: string; gppSection?: GPPSection } => {
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

  if (gppSection && usApproach === GPPUSApproach.ALL) {
    // if we're using the "all" approach, and the current state is supported but no notices are provided for that state, we should default to national.
    const hasNoticesForRegion = notices.some((notice) =>
      notice.gpp_field_mapping?.find((fm) => fm.region === experienceRegion),
    );
    if (!hasNoticesForRegion) {
      gppRegion = US_NATIONAL_REGION;
      gppSection = FIDES_US_REGION_TO_GPP_SECTION[gppRegion];
    }
  }

  if (
    !gppSection ||
    (gppRegion === US_NATIONAL_REGION && usApproach === GPPUSApproach.STATE)
  ) {
    return {};
  }
  return { gppRegion, gppSection };
};

const setNoticesProvided: CmpApiUpdater = ({
  cmpApi,
  gppRegion,
  gppSection,
  experience,
}) => {
  const { privacy_notices: notices = [] } = experience;
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
};

const setOptOuts: CmpApiUpdater = ({
  cmpApi,
  gppRegion,
  gppSection,
  experience,
  cookie,
}) => {
  if (!cookie) {
    return;
  }
  const { privacy_notices: notices = [] } = experience;
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
};

const updateGpp = (
  updater: CmpApiUpdater,
  {
    cmpApi,
    experience,
    cookie,
  }: {
    cmpApi: CmpApi;
    experience: PrivacyExperience;
    cookie?: FidesCookie;
  },
) => {
  const { gppRegion, gppSection } = getGppSectionAndRegion(experience);

  if (!gppRegion || !gppSection) {
    // If we don't have a section, we can't set anything.
    // If we're using the state approach we shouldn't return the national section, even if region is set to national.
    return [];
  }

  const sectionsChanged = new Set<GPPSection>();
  sectionsChanged.add(gppSection);

  updater({ cmpApi, gppRegion, gppSection, experience, cookie });

  const { gpp_settings: gppSettings } = experience;
  setMspaSections({ cmpApi, sectionName: gppSection.name, gppSettings });

  return Array.from(sectionsChanged);
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
}) => updateGpp(setNoticesProvided, { cmpApi, experience });

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
}) => updateGpp(setOptOuts, { cmpApi, cookie, experience });
