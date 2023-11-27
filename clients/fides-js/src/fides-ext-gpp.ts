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
      cmpApi.setSignalStatus(SignalStatus.READY);
    }
  });

  window.addEventListener("FidesUIShown", () => {
    cmpApi.setSignalStatus(SignalStatus.NOT_READY);
    cmpApi.setCmpDisplayStatus(CmpDisplayStatus.VISIBLE);
  });

  window.addEventListener("FidesModalClosed", (event) => {
    cmpApi.setCmpDisplayStatus(CmpDisplayStatus.HIDDEN);
    // If the modal was closed without the user saving, set signal status back to Ready
    if (
      event.detail.extraDetails &&
      event.detail.extraDetails.saved === false
    ) {
      cmpApi.setSignalStatus(SignalStatus.READY);
    }
  });

  window.addEventListener("FidesUpdated", (event) => {
    const tcString = extractTCStringForCmpApi(event);
    // Workaround for bug in base library https://github.com/IABTechLab/iabgpp-es/issues/35
    cmpApi.setFieldValueBySectionId(TCF_SECTION_ID, "CmpId", ETHYCA_CMP_ID);
    cmpApi.setSectionStringById(TCF_SECTION_ID, tcString ?? "");
    cmpApi.fireSectionChange("tcfeuv2");
    cmpApi.setSignalStatus(SignalStatus.READY);
  });
};

initializeGppCmpApi();
