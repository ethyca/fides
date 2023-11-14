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

const CMP_ID = 407; // TODO: is this supposed to be the same as TCF, or is this separate?
const CMP_VERSION = 1;
const TCF_VERSION = 2;

const TCF_SECTION_ID = 2;

export const initializeGppCmpApi = () => {
  makeStub();

  const cmpApi = new CmpApi(CMP_ID, CMP_VERSION);
  cmpApi.setApplicableSections([TCF_SECTION_ID]);
  cmpApi.setCmpStatus(CmpStatus.LOADED);
  cmpApi.setSignalStatus(SignalStatus.READY);

  if (window.__tcfapi) {
    window.__tcfapi("addEventListener", TCF_VERSION, (tcData, success) => {
      if (!success) {
        return;
      }
      if (tcData.eventStatus === "cmpuishown") {
        cmpApi.setCmpDisplayStatus(CmpDisplayStatus.VISIBLE);
      }
      if (tcData.eventStatus === "useractioncomplete") {
        cmpApi.setCmpDisplayStatus(CmpDisplayStatus.HIDDEN);
      }
      // Workaround for bug in base library https://github.com/IABTechLab/iabgpp-es/issues/35
      cmpApi.setFieldValueBySectionId(TCF_SECTION_ID, "CmpId", CMP_ID);
      const { tcString } = tcData;
      cmpApi.setSectionStringById(TCF_SECTION_ID, tcString);
      cmpApi.fireSectionChange("tcfeuv2");
    });
  }
};

initializeGppCmpApi();
