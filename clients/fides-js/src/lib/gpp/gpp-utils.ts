/**
 * @fileoverview GPP utility functions for handling Global Privacy Platform operations.
 *
 * ⚠️  IMPORTANT: This file is synchronized between repositories!
 *
 * This file exists in both:
 * - fides: clients/fides-js/src/lib/gpp/gpp-utils.ts
 * - fidesplus: src/fidesplus/gpp_js_integration/gpp-utils.ts
 *
 * Any changes made to this file should be applied to both locations
 * to maintain consistency between the open-source and enterprise versions.
 */

import { UsNatField } from "@iabgpp/cmpapi";

import { FIDES_US_REGION_TO_GPP_SECTION, GPPUSApproach } from "./constants";
import { GPPSection, GPPSettings, NoticeConsent, PrivacyNotice } from "./types";

export const US_NATIONAL_REGION = "us";

/**
 * Checks if a given region is in the US based on the provided region string's prefix.
 * Also returns true if the region is the US_NATIONAL_REGION.
 */
export const isUsRegion = (region: string) =>
  region?.toLowerCase().startsWith("us");

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

/**
 * Generic interface for GPP API objects that can set field values
 */
export interface GPPApiLike {
  setFieldValue(
    sectionName: string,
    field: string,
    value: number | number[],
  ): void;
}

/**
 * Sets MSPA sections on a GPP API object (works with both GppModel and CmpApi)
 */
export const setMspaSections = ({
  gppApi,
  sectionName,
  gppSettings,
}: {
  gppApi: GPPApiLike;
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

    gppApi.setFieldValue(sectionName, cmpApiField, value);
  });
};

/**
 * Common logic for determining GPP section and region from a privacy experience
 */
export const getGppSectionAndRegion = (
  experienceRegion: string,
  usApproach: GPPUSApproach | undefined,
  notices: Array<{ gpp_field_mapping?: Array<{ region: string }> }> = [],
): { gppRegion?: string; gppSection?: GPPSection } => {
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
    // If we don't have a section, we can't set anything.
    // If we're using the state approach we shouldn't return the national section, even if region is set to national.
    return {};
  }

  return { gppRegion, gppSection };
};

export interface CmpApiUpdaterProps {
  gppApi: GPPApiLike;
  gppRegion: string;
  gppSection: GPPSection;
  privacyNotices: PrivacyNotice[];
  noticeConsent?: NoticeConsent;
}

export const setOptOuts = ({
  gppApi,
  gppRegion,
  gppSection,
  privacyNotices,
  noticeConsent,
}: CmpApiUpdaterProps) => {
  if (!noticeConsent) {
    return;
  }
  privacyNotices.forEach((privacyNotice) => {
    const { notice_key: noticeKey, gpp_field_mapping: fieldMapping } =
      privacyNotice;
    const consentValue = noticeConsent[noticeKey];
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
        gppApi.setFieldValue(gppSection.name, gppMechanism.field, valueAsNum);
      });
    }
  });
};

export const setNoticesProvided = ({
  gppApi,
  gppRegion,
  gppSection,
  privacyNotices,
}: CmpApiUpdaterProps) => {
  privacyNotices.forEach((notice) => {
    const { gpp_field_mapping: fieldMapping } = notice;
    const gppNotices = fieldMapping?.find(
      (fm) => fm.region === gppRegion,
    )?.notice;
    if (gppNotices) {
      gppNotices.forEach((gppNotice) => {
        // 1 means notice was provided
        gppApi.setFieldValue(gppSection.name, gppNotice, 1);
      });
    }
  });
};
