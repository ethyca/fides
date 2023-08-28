/**
 * This file is responsible for all TCF specific logic. It does not get bundled in with
 * vanilla fides-js, since all of its actions are very TCF specific.
 *
 * In the future, this should hold interactions with the CMP API as well as string generation.
 */

import { CmpApi } from "@iabtechlabtcf/cmpapi";
import {
  TCModel,
  TCString,
  GVL,
  VersionOrVendorList,
} from "@iabtechlabtcf/core";
import { transformUserPreferenceToBoolean } from "./consent-utils";
import gvlJson from "./tcf/gvl.json";
import { TcfSavePreferences } from "./tcf/types";
import { vendorIsGvl } from "./tcf/vendors";

const CMP_ID = 12; // TODO: hardcode our unique CMP ID after certification
const CMP_VERSION = 1;

/**
 * Generate TC String based on TCF-related info from privacy experience.
 * Called when there is either a FidesInitialized or FidesUpdated event
 */
export const generateTcString = async (
  tcStringPreferences?: TcfSavePreferences
): Promise<string> => {
  // Creates a new TC string based on an old GVL version
  // (https://vendor-list.consensu.org/v2/archives/vendor-list-v1.json)
  // due to TCF library not yet supporting latest GVL (https://vendor-list.consensu.org/v3/vendor-list.json).
  // We'll need to update this with our own hosted GVL once the lib is updated
  // https://github.com/InteractiveAdvertisingBureau/iabtcf-es/pull/389
  const tcModel = new TCModel(new GVL(gvlJson as VersionOrVendorList));

  let encodedString = "";

  // Some fields will not be populated until a GVL is loaded
  await tcModel.gvl.readyPromise;

  tcModel.cmpId = CMP_ID;
  tcModel.cmpVersion = CMP_VERSION;
  tcModel.consentScreen = 1; // todo- On which 'screen' consent was captured; this is a CMP proprietary number encoded into the TC string

  if (tcStringPreferences) {
    // todo- when we set vendorLegitimateInterests, make sure we never set purposes 1, 3, 4, 5 and 6
    if (
      tcStringPreferences.vendor_preferences &&
      tcStringPreferences.vendor_preferences.length > 0
    ) {
      tcStringPreferences.vendor_preferences.forEach((vendorPreference) => {
        const consented = transformUserPreferenceToBoolean(
          vendorPreference.preference
        );
        if (consented && vendorIsGvl(vendorPreference)) {
          tcModel.vendorConsents.set(+vendorPreference.id);
        }
      });
    }

    // Set purpose consent on tcModel
    if (
      tcStringPreferences.purpose_preferences &&
      tcStringPreferences.purpose_preferences.length > 0
    ) {
      tcStringPreferences.purpose_preferences.forEach((purposePreference) => {
        const consented = transformUserPreferenceToBoolean(
          purposePreference.preference
        );
        if (consented) {
          tcModel.purposeConsents.set(+purposePreference.id);
        }
      });
    }

    // Set special feature opt-ins on tcModel
    if (
      tcStringPreferences.special_feature_preferences &&
      tcStringPreferences.special_feature_preferences.length > 0
    ) {
      tcStringPreferences.special_feature_preferences.forEach(
        (specialFeaturePreference) => {
          const consented = transformUserPreferenceToBoolean(
            specialFeaturePreference.preference
          );
          if (consented) {
            tcModel.purposeConsents.set(+specialFeaturePreference.id);
          }
        }
      );
    }

    // note that we cannot set consent for special purposes nor features because the IAB policy states
    // the user is not given choice by a CMP.
    // See https://iabeurope.eu/iab-europe-transparency-consent-framework-policies/
    // and https://github.com/InteractiveAdvertisingBureau/iabtcf-es/issues/63#issuecomment-581798996
    encodedString = TCString.encode(tcModel);
  }
  return Promise.resolve(encodedString);
};

/**
 * Call tcf() to configure Fides with tcf support (if tcf is enabled).
 */
export const tcf = () => {
  const isServiceSpecific = true; // TODO: determine this from the backend?
  const cmpApi = new CmpApi(CMP_ID, CMP_VERSION, isServiceSpecific);
  console.log("adding event listeners for tcf");
  window.addEventListener("FidesInitialized", (event) => {
    const { tcString } = event.detail;
    console.log(`fidesinitialized with tcstring: ${tcString}`);
    cmpApi.update(tcString ?? null);
  });
  window.addEventListener("FidesUIShown", (event) => {
    const { tcString } = event.detail;
    console.log(`fidesuishown with tcstring: ${tcString}`);
    cmpApi.update(tcString ?? null, true);
  });
  // TODO: need FidesUIClosed ?
  window.addEventListener("FidesUpdated", (event) => {
    const { tcString } = event.detail;
    console.log(`fidesupdated with tcstring: ${tcString}`);
    cmpApi.update(tcString ?? null, false);
  });
};
