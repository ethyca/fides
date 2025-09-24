/**
 * Helper functions to set the GPP CMP API based on Fides values
 */

import { CmpApi } from "@iabgpp/cmpapi";

import type { ConsentContext } from "../consent-context";
import { FidesCookie, PrivacyExperience } from "../consent-types";
import {
  CmpApiUpdaterProps,
  getGppSectionAndRegion,
  setGpcSubsection,
  setMspaSections,
  setNoticesProvided,
  setOptOuts,
} from "./gpp-utils";
import { GPPSection } from "./types";

interface UpdateGppProps {
  cmpApi: CmpApi;
  experience: PrivacyExperience;
  context: ConsentContext;
  cookie?: FidesCookie;
}
const updateGpp = (
  updater: (props: CmpApiUpdaterProps) => void,
  { cmpApi, experience, context, cookie }: UpdateGppProps,
) => {
  const { gppRegion, gppSection } = getGppSectionAndRegion(experience);

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

  // Set the MSPA fields with the current settings
  const { gpp_settings: gppSettings } = experience;
  setMspaSections({
    gppApi: cmpApi,
    sectionName: gppSection.name,
    gppSettings,
  });

  // Set the GPC subsection (if supported) with the current GPC context
  setGpcSubsection({
    gppApi: cmpApi,
    gppSection,
    context,
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
  context,
}: {
  cmpApi: CmpApi;
  experience: PrivacyExperience;
  context: ConsentContext;
}) => updateGpp(setNoticesProvided, { cmpApi, experience, context });

/**
 * Sets the appropriate fields on a GPP CMP API model for user opt-outs
 *
 * Returns GPP sections which were updated
 */
export const setGppOptOutsFromCookieAndExperience = ({
  cmpApi,
  cookie,
  experience,
  context,
}: {
  cmpApi: CmpApi;
  cookie: FidesCookie;
  experience: PrivacyExperience;
  context: ConsentContext;
}) => updateGpp(setOptOuts, { cmpApi, cookie, experience, context });
