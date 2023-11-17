/* eslint-disable no-underscore-dangle */
/**
 * Extension for GPP
 *
 * Usage:
 * Include as a script tag as early as possible (even before fides.js)
 */

import {
  CmpApi,
  CmpDisplayStatus,
  CmpStatus,
  SignalStatus,
} from "@iabgpp/cmpapi";
import { makeStub } from "../lib/gpp/stub";
import { fidesEventToTcString } from "../lib/tcf/events";
import {
  isPrivacyExperience,
  shouldResurfaceConsent,
} from "../lib/consent-utils";

const CMP_ID = 407; // TODO: is this supposed to be the same as TCF, or is this separate?
const CMP_VERSION = 1;

const TCF_SECTION_ID = 2;

export const initializeGppCmpApi = () => {
  makeStub();

  const cmpApi = new CmpApi(CMP_ID, CMP_VERSION);
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

  window.addEventListener("FidesModalClosed", () => {
    cmpApi.setCmpDisplayStatus(CmpDisplayStatus.HIDDEN);
  });

  window.addEventListener("FidesUpdated", (event) => {
    const tcString = fidesEventToTcString(event);
    // Workaround for bug in base library https://github.com/IABTechLab/iabgpp-es/issues/35
    cmpApi.setFieldValueBySectionId(TCF_SECTION_ID, "CmpId", CMP_ID);
    cmpApi.setSectionStringById(TCF_SECTION_ID, tcString ?? "");
    cmpApi.fireSectionChange("tcfeuv2");
    cmpApi.setSignalStatus(SignalStatus.READY);
  });
};

initializeGppCmpApi();
