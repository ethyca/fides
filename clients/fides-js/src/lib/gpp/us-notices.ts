/**
 * Helper functions to set the GPP CMP API based on Fides values
 */

import { CmpApi, UsNatV1Field } from "@iabgpp/cmpapi";

import { FIDES_REGION_TO_GPP_SECTION } from "./constants";
import { FidesCookie, PrivacyExperience } from "../consent-types";
import { GPPSettings } from "./types";

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
      cmpApiField: UsNatV1Field.MSPA_COVERED_TRANSACTION,
    },
    {
      gppSettingField: gppSettings.mspa_opt_out_option_mode,
      cmpApiField: UsNatV1Field.MSPA_OPT_OUT_OPTION_MODE,
    },
    {
      gppSettingField: gppSettings.mspa_service_provider_mode,
      cmpApiField: UsNatV1Field.MSPA_SERVICE_PROVIDER_MODE,
    },
  ];
  mspaFields.forEach(({ gppSettingField, cmpApiField }) => {
    cmpApi.setFieldValue(sectionName, cmpApiField, gppSettingField ? 1 : 2);
  });
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
  const sectionsChanged = new Set<{ name: string; id: number }>();
  const {
    privacy_notices: notices = [],
    region,
    gpp_settings: gppSettings,
  } = experience;
  const gppSection = FIDES_REGION_TO_GPP_SECTION[region];

  if (!gppSection) {
    return [];
  }

  sectionsChanged.add(gppSection);

  notices.forEach((notice) => {
    const { gpp_field_mapping: fieldMapping } = notice;
    const gppNotices = fieldMapping?.find((fm) => fm.region === region)?.notice;
    if (gppNotices) {
      gppNotices.forEach((gppNotice) => {
        // 1 means notice was provided
        cmpApi.setFieldValue(gppSection.name, gppNotice, 1);
      });
    }
  });

  // Set MSPA
  setMspaSections({ cmpApi, sectionName: gppSection.name, gppSettings });

  // Set all other *Notice fields to 2
  const section = cmpApi.getSection(gppSection.name);
  const sectionNoticeKeys = Object.keys(section).filter((key) =>
    key.endsWith("Notice")
  );
  sectionNoticeKeys.forEach((sectionKey) => {
    const curValue = cmpApi.getFieldValue(gppSection.name, sectionKey);
    if (curValue !== 1) {
      cmpApi.setFieldValue(gppSection.name, sectionKey, 2);
    }
  });

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
  const sectionsChanged = new Set<{ name: string; id: number }>();
  const { consent } = cookie;
  const gppSection = FIDES_REGION_TO_GPP_SECTION[experience.region];

  if (!gppSection) {
    return [];
  }
  sectionsChanged.add(gppSection);

  const noticeKeys = Object.keys(consent);
  noticeKeys.forEach((noticeKey) => {
    const privacyNotice = experience.privacy_notices?.find(
      (n) => n.notice_key === noticeKey
    );
    const consentValue = consent[noticeKey];
    if (privacyNotice) {
      const { gpp_field_mapping: fieldMapping } = privacyNotice;
      const gppMechanisms = fieldMapping?.find(
        (fm) => fm.region === experience.region
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
    gppSettings: experience.gpp_settings,
  });

  return Array.from(sectionsChanged);
};
