/* eslint-disable no-underscore-dangle */
/**
 * Extension for GPP
 *
 * Usage:
 * Dynamically imported by fides.js as an extension
 */

import {
  CmpApi,
  CmpDisplayStatus,
  CmpStatus,
  SignalStatus,
  TcfEuV2,
  UsNat,
} from "@iabgpp/cmpapi";

import { FidesEvent } from "./fides";
import {
  FidesGlobal,
  FidesOptions,
  NoticeConsent,
  PrivacyNoticeWithPreference,
} from "./lib/consent-types";
import {
  allNoticesAreDefaultOptIn,
  isPrivacyExperience,
  shouldResurfaceConsent,
} from "./lib/consent-utils";
import { saveFidesCookie } from "./lib/cookie";
import { formatFidesStringWithGpp } from "./lib/fidesString";
import {
  CMP_VERSION,
  FIDES_US_REGION_TO_GPP_SECTION,
} from "./lib/gpp/constants";
import { fidesStringToConsent } from "./lib/gpp/string-to-consent";
import { makeStub } from "./lib/gpp/stub";
import { GppFunction, GPPUSApproach } from "./lib/gpp/types";
import {
  setGppNoticesProvidedFromExperience,
  setGppOptOutsFromCookieAndExperience,
} from "./lib/gpp/us-notices";
import { ETHYCA_CMP_ID } from "./lib/tcf/constants";
import { extractTCStringForCmpApi } from "./lib/tcf/events";

declare global {
  interface Window {
    Fides: FidesGlobal;
    config: {
      // DEFER (PROD-1243): support a configurable "custom options" path
      tc_info: FidesOptions;
    };
    __gpp?: GppFunction;
    __gppLocator?: Window;
  }
}

/**
 * Special GPP util method to determine if user has existing prefs, including those on the cookie or fides string.
 * Specifically, this method does not consider legacy consent has an existing pref, since they aren't relevant for GPP.
 * @param savedConsent: NoticeConsent | undefined
 * @param fides_string: string | undefined
 * @param notices: Array<PrivacyNoticeWithPreference> | undefined
 * @return boolean
 */
const userHasExistingPrefs = (
  savedConsent: NoticeConsent | undefined,
  fides_string: string | undefined,
  notices: Array<PrivacyNoticeWithPreference> | undefined,
): boolean => {
  if (!savedConsent) {
    return false;
  }
  if (fides_string) {
    return true;
  }
  return Boolean(
    notices &&
      Object.entries(savedConsent).some(
        ([key, val]) =>
          key in notices.map((i) => i.notice_key) && val !== undefined,
      ),
  );
};

/**
 * Wrapper around setting a TC string on the CMP API object.
 * Returns whether or not the TC string was set.
 * @param event: FidesEvent
 * @param cmpApi: the CMP API model
 */
const setTcString = (event: FidesEvent, cmpApi: CmpApi): boolean => {
  if (!isPrivacyExperience(window.Fides.experience)) {
    return false;
  }
  const { gpp_settings: gppSettings } = window.Fides.experience;
  if (!window.Fides.options.tcfEnabled || !gppSettings?.enable_tcfeu_string) {
    return false;
  }
  const tcString = extractTCStringForCmpApi(event);
  if (!tcString) {
    return false;
  }
  // Workaround for bug in base library https://github.com/IABTechLab/iabgpp-es/issues/35
  cmpApi.setFieldValueBySectionId(TcfEuV2.ID, "CmpId", ETHYCA_CMP_ID);
  cmpApi.setSectionStringById(TcfEuV2.ID, tcString);
  return true;
};

/** From our options, derive what APIs of GPP are applicable */
const getSupportedApis = () => {
  const experienceSupportedApis: string[] = [];
  if (isPrivacyExperience(window.Fides.experience)) {
    const { gpp_settings: gppSettings } = window.Fides.experience;
    if (gppSettings && gppSettings.enabled) {
      if (window.Fides.options.tcfEnabled && gppSettings.enable_tcfeu_string) {
        experienceSupportedApis.push(`${TcfEuV2.ID}:${TcfEuV2.NAME}`);
      }
      fidesDebugger("GPP settings", gppSettings);
      if (
        gppSettings.us_approach === GPPUSApproach.NATIONAL ||
        gppSettings.us_approach === GPPUSApproach.ALL
      ) {
        fidesDebugger("GPP: setting US National APIs");
        experienceSupportedApis.push(`${UsNat.ID}:${UsNat.NAME}`);
      }
      if (
        gppSettings.us_approach === GPPUSApproach.STATE ||
        gppSettings.us_approach === GPPUSApproach.ALL
      ) {
        fidesDebugger("GPP: setting US State APIs");
        // TODO: include the states based off of locations/regulations.
        // For now, use all of them. https://ethyca.atlassian.net/browse/PROD-1595
        Object.values(FIDES_US_REGION_TO_GPP_SECTION).forEach((state) => {
          if (state.id !== UsNat.ID) {
            experienceSupportedApis.push(`${state.id}:${state.name}`);
          }
        });
      }
    }
  }
  return experienceSupportedApis;
};

const initializeGppCmpApi = () => {
  makeStub();
  const cmpApi = new CmpApi(ETHYCA_CMP_ID, CMP_VERSION);
  cmpApi.setCmpStatus(CmpStatus.LOADED);
  window.addEventListener("FidesInitialized", (event) => {
    const { experience, saved_consent: savedConsent, options } = window.Fides;
    const experienceSupportedApis = getSupportedApis();

    // Set up supported APIs before validating experience since getSupportedApis() needs it
    cmpApi.setSupportedAPIs(experienceSupportedApis);

    if (!isPrivacyExperience(experience)) {
      return;
    }

    // Check for fides_string override in options and set consent preferences if present.
    const { fidesString } = options;
    if (fidesString) {
      fidesStringToConsent({
        fidesString,
        cmpApi,
      });
    }

    // When there's no fides_string, determine if we should immediately set up the GPP state and mark it as ready.
    // We proceed if EITHER:
    // 1. Consent should not be resurfaced (i.e., user has valid consent that hasn't expired)
    //    OR
    // 2. ALL of these conditions are met:
    //    - TCF is disabled (not using TCF EU consent)
    //    - All notices in the experience default to opt-in
    //    - User has no existing preferences (either in cookie, fides_string, or mapped to notices)
    if (
      !fidesString &&
      (!shouldResurfaceConsent(experience, event.detail, savedConsent) ||
        (!options.tcfEnabled &&
          allNoticesAreDefaultOptIn(experience.privacy_notices) &&
          !userHasExistingPrefs(
            savedConsent,
            event.detail.fides_string,
            experience.privacy_notices,
          )))
    ) {
      const tcSet = setTcString(event, cmpApi);
      if (tcSet) {
        cmpApi.setApplicableSections([TcfEuV2.ID]);
      }
      const sectionsSet = setGppNoticesProvidedFromExperience({
        cmpApi,
        experience,
      });
      const sectionsChanged = setGppOptOutsFromCookieAndExperience({
        cmpApi,
        cookie: event.detail,
        experience,
      });
      if (sectionsChanged.length) {
        cmpApi.setApplicableSections(sectionsChanged.map((s) => s.id));
      }
      if (!tcSet && !sectionsSet.length && !sectionsChanged.length) {
        cmpApi.setApplicableSections([-1]);
      }
      cmpApi.setSignalStatus(SignalStatus.READY);
      const newFidesString = formatFidesStringWithGpp(cmpApi);
      window.Fides.fides_string = newFidesString;
      fidesDebugger("GPP: updated fides_string", newFidesString);
    }

    if (window.Fides.options.debug && typeof window?.__gpp === "function") {
      window?.__gpp?.("ping", (data) => {
        fidesDebugger("GPP Ping Data:", data);
      });
    }
  });

  window.addEventListener("FidesUIShown", (event) => {
    // Set US GPP notice fields
    const { experience, saved_consent: savedConsent, options } = window.Fides;
    if (isPrivacyExperience(experience)) {
      // set signal status to ready only for users with no existing prefs and if notices are all opt-in by default and TCF is disabled
      if (
        !options.tcfEnabled &&
        allNoticesAreDefaultOptIn(experience.privacy_notices) &&
        !userHasExistingPrefs(
          savedConsent,
          event.detail.fides_string,
          experience.privacy_notices,
        )
      ) {
        cmpApi.setSignalStatus(SignalStatus.READY);
      } else {
        cmpApi.setSignalStatus(SignalStatus.NOT_READY);
      }
      cmpApi.setCmpDisplayStatus(CmpDisplayStatus.VISIBLE);
      const sectionsChanged = setGppNoticesProvidedFromExperience({
        cmpApi,
        experience,
      });
      if (sectionsChanged.length) {
        cmpApi.setApplicableSections(sectionsChanged.map((s) => s.id));
        sectionsChanged.forEach((section) => {
          cmpApi.fireSectionChange(section.name);
        });
      }
    }
  });

  window.addEventListener("FidesModalClosed", (event) => {
    // If the modal was closed without the user saving, set signal status back to Ready
    // Let the FidesUpdated listener below handle setting the display status to hidden for other cases
    if (
      event.detail.extraDetails &&
      event.detail.extraDetails.saved === false
    ) {
      cmpApi.setCmpDisplayStatus(CmpDisplayStatus.HIDDEN);
      cmpApi.setSignalStatus(SignalStatus.READY);
    }
  });

  window.addEventListener("FidesUpdated", (event) => {
    // In our flows, whenever FidesUpdated fires, the UI has closed
    cmpApi.setCmpDisplayStatus(CmpDisplayStatus.HIDDEN);
    const tcSet = setTcString(event, cmpApi);
    if (tcSet) {
      cmpApi.setApplicableSections([TcfEuV2.ID]);
      cmpApi.fireSectionChange("tcfeuv2");
    }

    // Set US GPP opt outs
    if (isPrivacyExperience(window.Fides.experience)) {
      const sectionsChanged = setGppOptOutsFromCookieAndExperience({
        cmpApi,
        cookie: event.detail,
        experience: window.Fides.experience,
      });
      if (sectionsChanged.length) {
        cmpApi.setApplicableSections(sectionsChanged.map((s) => s.id));
        sectionsChanged.forEach((section) => {
          cmpApi.fireSectionChange(section.name);
        });
      }

      // Update fides_string with GPP string
      const fidesString = formatFidesStringWithGpp(cmpApi);
      if (window.Fides.cookie) {
        window.Fides.fides_string = fidesString;
        window.Fides.cookie.fides_string = fidesString;
        saveFidesCookie(window.Fides.cookie, window.Fides.options.base64Cookie);
        fidesDebugger("GPP: updated fides_string", fidesString);
      }
    }
    cmpApi.setSignalStatus(SignalStatus.READY);
  });
};
window.addEventListener("FidesInitializing", (event) => {
  if (event.detail.extraDetails?.gppEnabled) {
    initializeGppCmpApi();
  }
});
