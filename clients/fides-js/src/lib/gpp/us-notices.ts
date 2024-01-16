/**
 * Helper functions to set the GPP CMP API based on Fides values
 */

import { CmpApi, UsNatV1, UsNatV1Field } from "@iabgpp/cmpapi";

import {
  FIDES_REGION_TO_GPP_SECTION,
  NOTICE_KEY_TO_FIDES_REGION_GPP_FIELDS,
} from "./constants";
import { FidesCookie, PrivacyExperience } from "../consent-types";

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
  if (gppSettings) {
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
      cmpApi.setFieldValue(
        gppSection.name,
        cmpApiField,
        gppSettingField ? 1 : 2
      );
    });
  }

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
export const setGppOptOutsFromCookie = ({
  cmpApi,
  cookie,
  region,
}: {
  cmpApi: CmpApi;
  cookie: FidesCookie;
  region: string;
}) => {
  const sectionsChanged = new Set<{ name: string; id: number }>();
  const { consent } = cookie;

  Object.entries(NOTICE_KEY_TO_FIDES_REGION_GPP_FIELDS).forEach(
    ([noticeKey, regionGppFields]) => {
      const gppFields = regionGppFields[region];
      if (gppFields) {
        const { gpp_mechanism_fields: fields } = gppFields;
        const consentValue = consent[noticeKey];

        const gppSection = FIDES_REGION_TO_GPP_SECTION[region];
        sectionsChanged.add(gppSection);
        fields.forEach((fieldObj) => {
          // In general, 0 = N/A, 1 = Opted out, 2 = Did not opt out
          let value = fieldObj.not_available; // if consentValue is undefined, we'll mark as N/A
          if (consentValue === false) {
            value = fieldObj.opt_out;
          } else if (consentValue) {
            value = fieldObj.not_opt_out;
          }
          cmpApi.setFieldValue(gppSection.name, fieldObj.field, value);
        });
      }
    }
  );

  return Array.from(sectionsChanged);
};
