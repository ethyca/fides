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
  UsCaV1,
  UsCoV1,
  UsCtV1,
  UsNatV1,
  UsUtV1,
  UsVaV1,
} from "@iabgpp/cmpapi";
import { makeStub } from "./lib/gpp/stub";
import { extractTCStringForCmpApi } from "./lib/tcf/events";
import {
  isPrivacyExperience,
  shouldResurfaceConsent,
} from "./lib/consent-utils";
import { ETHYCA_CMP_ID } from "./lib/tcf/constants";
import type { Fides } from "./lib/initialize";
import type { OverrideOptions } from "./lib/consent-types";
import { GPPUSApproach, GppFunction } from "./lib/gpp/types";
import { FidesEvent } from "./fides";
import {
  setGppNoticesProvidedFromExperience,
  setGppOptOutsFromCookie,
} from "./lib/gpp/us-notices";

const CMP_VERSION = 1;

declare global {
  interface Window {
    Fides: Fides;
    config: {
      // DEFER (PROD-1243): support a configurable "custom options" path
      tc_info: OverrideOptions;
    };
    __gpp?: GppFunction;
    __gppLocator?: Window;
  }
}

/**
 * Wrapper around setting a TC string on the CMP API object.
 * Returns whether or not the TC string was set.
 * @param event: FidesEvent
 * @param cmpApi: the CMP API model
 */
const setTcString = (event: FidesEvent, cmpApi: CmpApi) => {
  if (!window.Fides.options.tcfEnabled) {
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
    if (gppSettings && gppSettings.enabled && gppSettings.enable_tc_string) {
      if (gppSettings.enable_tc_string) {
        supportedApis.push(`${TcfEuV2.ID}:${TcfEuV2.NAME}`);
      }
      if (gppSettings.us_approach === GPPUSApproach.NATIONAL) {
        supportedApis.push(`${UsNatV1.ID}:${UsNatV1.NAME}`);
      }
      if (gppSettings.us_approach === GPPUSApproach.STATE) {
        // TODO: include the states based off of locations/regulations.
        // For now, hard code all of them.
        [UsCaV1, UsCoV1, UsCtV1, UsUtV1, UsVaV1].forEach((state) => {
          supportedApis.push(`${state.ID}:${state.NAME}`);
        });
      }
    }
  }
  return supportedApis;
};

export const initializeGppCmpApi = () => {
  makeStub();
  const cmpApi = new CmpApi(ETHYCA_CMP_ID, CMP_VERSION);
  cmpApi.setCmpStatus(CmpStatus.LOADED);
  // If consent does not need to be resurfaced, then we can set the signal to Ready here
  window.addEventListener("FidesInitialized", (event) => {
    const { experience } = window.Fides;
    cmpApi.setSupportedAPIs(getSupportedApis());
    if (
      isPrivacyExperience(experience) &&
      !shouldResurfaceConsent(experience, event.detail)
    ) {
      const tcSet = setTcString(event, cmpApi);
      if (tcSet) {
        cmpApi.setApplicableSections([TcfEuV2.ID]);
      }
      setGppNoticesProvidedFromExperience({ cmpApi, experience });
      const sectionsChanged = setGppOptOutsFromCookie({
        cmpApi,
        cookie: event.detail,
        region: experience.region,
      });
      if (sectionsChanged.length) {
        cmpApi.setApplicableSections(sectionsChanged.map((s) => s.id));
      }
      cmpApi.setSignalStatus(SignalStatus.READY);
    }
  });

  window.addEventListener("FidesUIShown", () => {
    cmpApi.setSignalStatus(SignalStatus.NOT_READY);
    cmpApi.setCmpDisplayStatus(CmpDisplayStatus.VISIBLE);

    // Set US GPP notice fields
    const { experience } = window.Fides;
    if (isPrivacyExperience(experience)) {
      const sectionsChanged = setGppNoticesProvidedFromExperience({
        cmpApi,
        experience,
      });
      cmpApi.setApplicableSections(sectionsChanged.map((s) => s.id));
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
    const sectionsChanged = setGppOptOutsFromCookie({
      cmpApi,
      cookie: event.detail,
      region: window.Fides.experience?.region ?? "",
    });
    if (sectionsChanged.length) {
      cmpApi.setApplicableSections(sectionsChanged.map((s) => s.id));
      sectionsChanged.forEach((section) => {
        cmpApi.fireSectionChange(section.name);
      });
    }
    cmpApi.setSignalStatus(SignalStatus.READY);
  });
};

initializeGppCmpApi();
