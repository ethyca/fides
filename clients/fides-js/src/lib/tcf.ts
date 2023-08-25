/**
 * This file is responsible for all TCF specific logic. It does not get bundled in with
 * vanilla fides-js, since all of its actions are very TCF specific.
 *
 * In the future, this should hold interactions with the CMP API as well as string generation.
 */

import { TCModel, TCString, GVL } from "@iabtechlabtcf/core";
import { PrivacyExperience } from "./consent-types";
import { transformUserPreferenceToBoolean } from "./consent-utils";
import gvlJson from "./tcf/GVL.json";
import { TcStringPreferences, TcfSavePreferences } from "./tcf/types";

export const buildTcStringPreferences = (
  experience?: PrivacyExperience
): TcStringPreferences => ({
  tcf_purposes: experience?.tcf_purposes
    ? new Map(experience.tcf_purposes.map((purpose) => [purpose.id, purpose]))
    : undefined,
  tcf_special_purposes: experience?.tcf_special_purposes
    ? new Map(
        experience.tcf_special_purposes.map((purpose) => [purpose.id, purpose])
      )
    : undefined,
  tcf_vendors: experience?.tcf_vendors
    ? new Map(experience.tcf_vendors.map((vendor) => [vendor.id, vendor]))
    : undefined,
  tcf_features: experience?.tcf_features
    ? new Map(experience.tcf_features.map((feature) => [feature.id, feature]))
    : undefined,
  tcf_special_features: experience?.tcf_special_features
    ? new Map(
        experience.tcf_special_features.map((feature) => [feature.id, feature])
      )
    : undefined,
});

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
  console.log("initilaize TC Model");
  const tcModel = new TCModel(new GVL(gvlJson));

  let encodedString = "";

  // Some fields will not be populated until a GVL is loaded
  await tcModel.gvl.readyPromise;

  tcModel.cmpId = 12; // todo - hardcode our unique cmp id
  tcModel.cmpVersion = 1;
  tcModel.consentScreen = 1; // todo- On which 'screen' consent was captured; this is a CMP proprietary number encoded into the TC string

  if (tcStringPreferences) {
    // todo- when we set vendorLegitimateInterests, make sure we never set purposes 1, 3, 4, 5 and 6
    // Set vendor consent on tcModel
    if (
      tcStringPreferences.vendor_preferences &&
      tcStringPreferences.vendor_preferences.length > 0
    ) {
      tcStringPreferences.vendor_preferences.forEach((vendorPreference) => {
        const consented = transformUserPreferenceToBoolean(
          vendorPreference.preference
        );
        if (consented) {
          // TODO: safely make sure this is a number!
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
          tcModel.vendorConsents.set(+purposePreference.id);
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
            tcModel.vendorConsents.set(+specialFeaturePreference.id);
          }
        }
      );
    }

    // note that we cannot set consent for special purposes nor features because the IAB policy states
    // the user is not given choice by a CMP.
    // See https://iabeurope.eu/iab-europe-transparency-consent-framework-policies/
    // and https://github.com/InteractiveAdvertisingBureau/iabtcf-es/issues/63#issuecomment-581798996

    console.log("encode string");
    console.log(tcModel);
    encodedString = TCString.encode(tcModel);
  }
  return Promise.resolve(encodedString);
};

/**
 * Call tcf() to configure Fides with tcf support (if tcf is enabled).
 */
export const tcf = () => {
  console.log("adding event listeners for tcf");
  // window.addEventListener("FidesInitialized", (event) => {
  //   generateTcString(event.detail.tcStringPreferences, event.detail.debug).then(
  //     (tcString) => {
  //       // do something with string
  //       console.log(`fidesinitialized with tcstring: ${tcString}`);
  //     }
  //   );
  // });

  // window.addEventListener("FidesUpdated", (event) => {
  //   generateTcString(event.detail.tcStringPreferences, event.detail.debug).then(
  //     (tcString) => {
  //       // do something with string
  //       console.log(`fidesupdated with tcstring: ${tcString}`);
  //     }
  //   );
  // });
};
