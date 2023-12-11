/**
 * Helper functions to set the GPP CMP API based on Fides values
 */

import { CmpApi } from "@iabgpp/cmpapi";

import { FidesCookie } from "../cookie";
import {
  FIDES_REGION_TO_GPP_SECTION_ID,
  NOTICE_KEY_TO_FIDES_REGION_GPP_FIELDS,
} from "./constants";
import { PrivacyExperience } from "../consent-types";

export const setGppNoticesProvidedFromExperience = ({
  cmpApi,
  experience,
}: {
  cmpApi: CmpApi;
  experience: PrivacyExperience;
}) => {
  const { privacy_notices: notices, region } = experience;

  Object.entries(NOTICE_KEY_TO_FIDES_REGION_GPP_FIELDS).forEach(
    ([noticeKey, regionGppFields]) => {
      const gppFields = regionGppFields[region];
      if (gppFields) {
        const { gpp_notice_fields: fields } = gppFields;
        const experienceHasNotice = !!notices?.find(
          (n) => n.notice_key === noticeKey
        );
        // 1 = Yes notice was provided, 2 = No, notice was not provided.
        // QUESTION: do we ever put 0 here?
        const value = experienceHasNotice ? 1 : 2;
        const gppSectionId = FIDES_REGION_TO_GPP_SECTION_ID[region];
        fields.forEach((field) => {
          cmpApi.setFieldValueBySectionId(gppSectionId, field, value);
        });
      }
    }
  );
};

export const setGppOptOutsFromCookie = ({
  cmpApi,
  cookie,
  region,
}: {
  cmpApi: CmpApi;
  cookie: FidesCookie;
  region: string;
}) => {
  const { consent } = cookie;

  Object.entries(NOTICE_KEY_TO_FIDES_REGION_GPP_FIELDS).forEach(
    ([noticeKey, regionGppFields]) => {
      const gppFields = regionGppFields[region];
      if (gppFields) {
        const { gpp_mechanism_fields: fields } = gppFields;
        const consentValue = consent[noticeKey];

        const gppSectionId = FIDES_REGION_TO_GPP_SECTION_ID[region];
        fields.forEach((fieldObj) => {
          // In general, 0 = N/A, 1 = Opted out, 2 = Did not opt out
          let value = fieldObj.not_available; // if consentValue is undefined, we'll mark as N/A
          if (consentValue === false) {
            value = fieldObj.opt_out;
          } else if (consentValue) {
            value = fieldObj.not_opt_out;
          }
          cmpApi.setFieldValueBySectionId(gppSectionId, fieldObj.field, value);
        });
      }
    }
  );
};
