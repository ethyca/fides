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
import { GppFunction } from "./lib/gpp/types";
import { FidesEvent } from "./fides";
import {
  setGppNoticesProvidedFromExperience,
  setGppOptOutsFromCookie,
} from "./lib/gpp/us-notices";

const CMP_VERSION = 1;

const TCF_SECTION_ID = 2;

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
 * Wrapper around setting a TC string on the CMP API object
 * @param event: FidesEvent
 * @param cmpApi: the CMP API model
 */
const setTcString = (event: FidesEvent, cmpApi: CmpApi) => {
  const tcString = extractTCStringForCmpApi(event);
  if (tcString) {
    // Workaround for bug in base library https://github.com/IABTechLab/iabgpp-es/issues/35
    cmpApi.setFieldValueBySectionId(TCF_SECTION_ID, "CmpId", ETHYCA_CMP_ID);
    cmpApi.setSectionStringById(TCF_SECTION_ID, tcString);
  }
};

export const initializeGppCmpApi = () => {
  makeStub();
  const cmpApi = new CmpApi(ETHYCA_CMP_ID, CMP_VERSION);
  cmpApi.setApplicableSections([TCF_SECTION_ID]);
  cmpApi.setCmpStatus(CmpStatus.LOADED);
  // If consent does not need to be resurfaced, then we can set the signal to Ready here
  window.addEventListener("FidesInitialized", (event) => {
    const { experience } = window.Fides;
    if (
      isPrivacyExperience(experience) &&
      !shouldResurfaceConsent(experience, event.detail)
    ) {
      setTcString(event, cmpApi);
      cmpApi.setSignalStatus(SignalStatus.READY);
    }
  });

  window.addEventListener("FidesUIShown", () => {
    cmpApi.setSignalStatus(SignalStatus.NOT_READY);
    cmpApi.setCmpDisplayStatus(CmpDisplayStatus.VISIBLE);

    // Set US GPP notice fields
    const { experience } = window.Fides;
    if (isPrivacyExperience(experience)) {
      setGppNoticesProvidedFromExperience({ cmpApi, experience });
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
    setTcString(event, cmpApi);
    cmpApi.fireSectionChange("tcfeuv2");
    cmpApi.setSignalStatus(SignalStatus.READY);

    // Set US GPP opt outs
    setGppOptOutsFromCookie({
      cmpApi,
      cookie: event.detail,
      region: window.Fides.experience?.region ?? "",
    });
  });
};

initializeGppCmpApi();
