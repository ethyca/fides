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
  UsCa,
  UsCo,
  UsCt,
  UsNat,
  UsUt,
  UsVa,
} from "@iabgpp/cmpapi";

import { FidesEvent } from "./fides";
import type {
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
import { makeStub } from "./lib/gpp/stub";
import { GppFunction, GPPUSApproach } from "./lib/gpp/types";
import {
  setGppNoticesProvidedFromExperience,
  setGppOptOutsFromCookieAndExperience,
} from "./lib/gpp/us-notices";
import { ETHYCA_CMP_ID } from "./lib/tcf/constants";
import { extractTCStringForCmpApi } from "./lib/tcf/events";

const CMP_VERSION = 1;

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
const setTcString = (event: FidesEvent, cmpApi: CmpApi) => {
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
  const supportedApis: string[] = [];
  if (isPrivacyExperience(window.Fides.experience)) {
    const { gpp_settings: gppSettings } = window.Fides.experience;
    if (gppSettings && gppSettings.enabled) {
      if (window.Fides.options.tcfEnabled && gppSettings.enable_tcfeu_string) {
        supportedApis.push(`${TcfEuV2.ID}:${TcfEuV2.NAME}`);
      }
      fidesDebugger("GPP settings", gppSettings);
      if (
        gppSettings.us_approach === GPPUSApproach.NATIONAL ||
        gppSettings.us_approach === GPPUSApproach.ALL
      ) {
        fidesDebugger("GPP: setting US National APIs");
        supportedApis.push(`${UsNat.ID}:${UsNat.NAME}`);
      }
      if (
        gppSettings.us_approach === GPPUSApproach.STATE ||
        gppSettings.us_approach === GPPUSApproach.ALL
      ) {
        fidesDebugger("GPP: setting US State APIs");
        // TODO: include the states based off of locations/regulations.
        // For now, hard code all of them. https://ethyca.atlassian.net/browse/PROD-1595
        [UsCa, UsCo, UsCt, UsUt, UsVa].forEach((state) => {
          supportedApis.push(`${state.ID}:${state.NAME}`);
        });
      }
    }
  }
  return supportedApis;
};

const initializeGppCmpApi = () => {
  makeStub();
  const cmpApi = new CmpApi(ETHYCA_CMP_ID, CMP_VERSION);
  cmpApi.setCmpStatus(CmpStatus.LOADED);
  window.addEventListener("FidesInitialized", (event) => {
    // TODO (PROD-1439): re-evaluate if GPP is "cheating" accessing window.Fides instead of using the event details only
    const {
      experience,
      saved_consent: savedConsent,
      options,
      geolocation,
    } = window.Fides;
    const isTcfEnabled = options.tcfEnabled;
    cmpApi.setSupportedAPIs(getSupportedApis());
    // Set status to ready immediately upon initialization, if either:
    // A. Consent should not be resurfaced
    // B. User has no prefs and has all opt-in notices and TCF is disabled
    if (
      isPrivacyExperience(experience) &&
      (!shouldResurfaceConsent(experience, event.detail, savedConsent) ||
        (!isTcfEnabled &&
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

      // mimics __gpp('ping', console.log);
      fidesDebugger(
        `GPP: CMP status and configuration for ${geolocation?.location}`,
        {
          cmpStatus: cmpApi.getCmpStatus(),
          cmpDisplayStatus: cmpApi.getCmpDisplayStatus(),
          signalStatus: cmpApi.getSignalStatus(),
          supportedAPIs: cmpApi.getSupportedAPIs(),
          applicableSections: cmpApi.getApplicableSections(),
          gppString: cmpApi.getGppString(),
          parsedSections: cmpApi.getObject(),
        },
      );
    }
  });

  window.addEventListener("FidesUIShown", (event) => {
    // Set US GPP notice fields
    const { experience, saved_consent: savedConsent, options } = window.Fides;
    const isTcfEnabled = options.tcfEnabled;
    if (isPrivacyExperience(experience)) {
      // set signal status to ready only for users with no existing prefs and if notices are all opt-in by default and TCF is disabled
      if (
        !isTcfEnabled &&
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
    }
    cmpApi.setSignalStatus(SignalStatus.READY);
  });
};
window.addEventListener("FidesInitializing", (event) => {
  if (event.detail.extraDetails?.gppEnabled) {
    initializeGppCmpApi();
  }
});
