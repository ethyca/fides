/**
 * Helper functions to set the GPP CMP API based on Fides values
 */

import { CmpApi } from "@iabgpp/cmpapi";

import { FidesCookie, PrivacyExperience } from "../consent-types";
import {
  CmpApiUpdaterProps,
  getGppSectionAndRegion,
  setMspaSections,
  setNoticesProvided,
  setOptOuts,
} from "./gpp-utils";
import { GPPSection } from "./types";

interface UpdateGppProps {
  cmpApi: CmpApi;
  experience: PrivacyExperience;
  cookie?: FidesCookie;
}
const updateGpp = (
  updater: (props: CmpApiUpdaterProps) => void,
  { cmpApi, experience, cookie }: UpdateGppProps,
) => {
  const { gppRegion, gppSection } = getGppSectionAndRegion(
    experience.region,
    experience.gpp_settings?.us_approach,
    experience.privacy_notices,
  );

  if (!gppRegion || !gppSection) {
    // If we don't have a section, we can't set anything.
    // If we're using the state approach we shouldn't return the national section, even if region is set to national.
    return [];
  }

  const sectionsChanged = new Set<GPPSection>();
  sectionsChanged.add(gppSection);

  updater({
    gppApi: cmpApi,
    gppRegion,
    gppSection,
    privacyNotices: experience.privacy_notices || [],
    noticeConsent: cookie?.consent,
  });

  const { gpp_settings: gppSettings } = experience;
  setMspaSections({
    gppApi: cmpApi,
    sectionName: gppSection.name,
    gppSettings,
  });

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
