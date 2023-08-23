/**
 * This file is responsible for all TCF specific logic. It does not get bundled in with
 * vanilla fides-js, since all of its actions are very TCF specific.
 *
 * In the future, this should hold interactions with the CMP API as well as string generation.
 */

import {TCModel, TCString, GVL} from '@iabtechlabtcf/core';
import {PrivacyExperience} from "~/lib/consent-types";
import {transformUserPreferenceToBoolean} from "~/lib/consent-utils";
import gvlJson from "./tcf/GVL.json"

/**
 * Generate TC String based on TCF-related info from privacy experience.
 * Called when there is either a FidesInitialized or FidesUpdated event
 */
export const generateTcString = (privacyExperience: PrivacyExperience | undefined, debug: boolean): string => {

  // Creates a new TC string based on an old GVL version
  // (https://vendor-list.consensu.org/v2/archives/vendor-list-v1.json)
  // due to TCF library not yet supporting latest GVL (https://vendor-list.consensu.org/v3/vendor-list.json).
  // We'll need to update this with our own hosted GVL once the lib is updated
  // https://github.com/InteractiveAdvertisingBureau/iabtcf-es/pull/389
  const tcModel = new TCModel(new GVL(gvlJson));

  let encodedString = ""

  // Some fields will not be populated until a GVL is loaded
  tcModel.gvl.readyPromise.then(() => {

    tcModel.cmpId = 12345 // todo - hard-code our unique cmp id
    tcModel.cmpVersion = 1 // todo - hard-code our CMPVersion
    tcModel.consentScreen = 1 // todo- On which 'screen' consent was captured; this is a CMP proprietary number encoded into the TC string

    if (privacyExperience) {
      // Set vendor consent on tcModel
      privacyExperience.tcf_vendors?.forEach(vendor => {
        if (transformUserPreferenceToBoolean(vendor.current_preference)) {
          tcModel.vendorConsents.set(parseInt(vendor.id, 10))
        } else if (transformUserPreferenceToBoolean(vendor.default_preference)) {
          tcModel.vendorConsents.set(parseInt(vendor.id, 10))
        }
      })

      // Set purpose consent on tcModel
      privacyExperience.tcf_purposes?.forEach((purpose => {
        if (transformUserPreferenceToBoolean(purpose.current_preference)) {
          tcModel.purposeConsents.set(purpose.id)
        } else if (transformUserPreferenceToBoolean(purpose.default_preference)) {
          tcModel.purposeConsents.set(purpose.id)
        }
      }))

      // Set special feature opt-ins on tcModel
      privacyExperience.tcf_special_features?.forEach((purpose => {
        if (transformUserPreferenceToBoolean(purpose.current_preference)) {
          tcModel.specialFeatureOptins.set(purpose.id)
        } else if (transformUserPreferenceToBoolean(purpose.default_preference)) {
          tcModel.specialFeatureOptins.set(purpose.id)
        }
      }))
      // note that we cannot set consent for special purposes nor features because the IAB policy states
      // the user is not given choice by a CMP.
      // See https://iabeurope.eu/iab-europe-transparency-consent-framework-policies/
      // and https://github.com/InteractiveAdvertisingBureau/iabtcf-es/issues/63#issuecomment-581798996
    }

    encodedString = TCString.encode(tcModel);

    if (debug) {
      console.log(encodedString); // TC string encoded begins with 'C'
    }

  });

  return encodedString;

}

/**
 * Call tcf() to configure Fides with tcf support (if tcf is enabled).
 */
export const tcf = () => {
  window.addEventListener("FidesInitialized", (event) =>
      generateTcString(event.detail.experience, event.detail.debug)
  );
  window.addEventListener("FidesUpdated", (event) =>
      generateTcString(event.detail.experience, event.detail.debug)
  );
};
