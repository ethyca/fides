/**
 * This file is responsible for all TCF specific logic. It does not get bundled in with
 * vanilla fides-js, since all of its actions are very TCF specific.
 *
 * In the future, this should hold interactions with the CMP API as well as string generation.
 */

import { CmpApi } from "@iabtechlabtcf/cmpapi";
import { TCModel, TCString, GVL } from "@iabtechlabtcf/core";
import { makeStub } from "./tcf/stub";

import { EnabledIds } from "./tcf/types";
import { vendorIsGvl } from "./tcf/vendors";
import { PrivacyExperience } from "./consent-types";

const CMP_ID = 12; // TODO: hardcode our unique CMP ID after certification
const CMP_VERSION = 1;
const FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS = [1, 3, 4, 5, 6];

/**
 * Generate TC String based on TCF-related info from privacy experience.
 * Called when there is either a FidesInitialized or FidesUpdated event
 */
export const generateTcString = async ({
  experience,
  tcStringPreferences,
}: {
  tcStringPreferences?: EnabledIds;
  experience: PrivacyExperience;
}): Promise<string> => {
  let encodedString = "";
  try {
    const tcModel = new TCModel(new GVL(experience.gvl));

    // Some fields will not be populated until a GVL is loaded
    await tcModel.gvl.readyPromise;

    tcModel.cmpId = CMP_ID;
    tcModel.cmpVersion = CMP_VERSION;
    tcModel.consentScreen = 1; // todo- On which 'screen' consent was captured; this is a CMP proprietary number encoded into the TC string

    if (tcStringPreferences) {
      if (
        tcStringPreferences.vendorsConsent &&
        tcStringPreferences.vendorsConsent.length > 0
      ) {
        tcStringPreferences.vendorsConsent.forEach((vendorId) => {
          if (vendorIsGvl({ id: vendorId }, experience.gvl)) {
            tcModel.vendorConsents.set(+vendorId);
          }
        });
        tcStringPreferences.vendorsLegint.forEach((vendorId) => {
          const thisVendor =
            experience.tcf_legitimate_interests_vendors?.filter(
              (v) => v.id === vendorId
            )[0];

          const vendorPurposes = thisVendor?.legitimate_interests_purposes;
          // Handle the case where a vendor has forbidden legint purposes set
          let skipSetLegInt = false;
          if (vendorPurposes) {
            const legIntPurposeIds = vendorPurposes.map((p) => p.id);
            if (
              legIntPurposeIds.filter((id) =>
                FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS.includes(id)
              ).length
            ) {
              skipSetLegInt = true;
            }
            if (!skipSetLegInt) {
              tcModel.vendorLegitimateInterests.set(+vendorId);
            }
          }
        });
      }

      // Set purpose consent on tcModel
      if (
        tcStringPreferences.purposesConsent &&
        tcStringPreferences.purposesConsent.length > 0
      ) {
        tcStringPreferences.purposesConsent.forEach((purposeId) => {
          tcModel.purposeConsents.set(+purposeId);
        });
      }
      if (
        tcStringPreferences.purposesLegint &&
        tcStringPreferences.purposesLegint.length > 0
      ) {
        tcStringPreferences.purposesLegint.forEach((purposeId) => {
          const id = +purposeId;
          if (!FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS.includes(id)) {
            tcModel.purposeLegitimateInterests.set(id);
          }
        });
      }

      // Set special feature opt-ins on tcModel
      if (
        tcStringPreferences.specialFeatures &&
        tcStringPreferences.specialFeatures.length > 0
      ) {
        tcStringPreferences.specialFeatures.forEach((id) => {
          tcModel.specialFeatureOptins.set(+id);
        });
      }

      // note that we cannot set consent for special purposes nor features because the IAB policy states
      // the user is not given choice by a CMP.
      // See https://iabeurope.eu/iab-europe-transparency-consent-framework-policies/
      // and https://github.com/InteractiveAdvertisingBureau/iabtcf-es/issues/63#issuecomment-581798996
      encodedString = TCString.encode(tcModel);
    }
  } catch (e) {
    // eslint-disable-next-line no-console
    console.error("Unable to instantiate GVL: ", e);
    return Promise.resolve("");
  }
  return Promise.resolve(encodedString);
};

/**
 * Call tcf() to configure Fides with tcf support (if tcf is enabled).
 */
export const tcf = () => {
  makeStub();
  const isServiceSpecific = true; // TODO: determine this from the backend?
  const cmpApi = new CmpApi(CMP_ID, CMP_VERSION, isServiceSpecific);

  // `null` value indicates that GDPR does not apply
  // Initialize api with TC str, we don't yet show UI, so we use false
  // see https://github.com/InteractiveAdvertisingBureau/iabtcf-es/tree/master/modules/cmpapi#dont-show-ui--tc-string-does-not-need-an-update
  window.addEventListener("FidesInitialized", (event) => {
    const { tc_string: tcString } = event.detail;
    cmpApi.update(tcString ?? null, false);
  });
  // UI is visible
  // see https://github.com/InteractiveAdvertisingBureau/iabtcf-es/tree/master/modules/cmpapi#show-ui--tc-string-needs-update
  // and https://github.com/InteractiveAdvertisingBureau/iabtcf-es/tree/master/modules/cmpapi#show-ui--new-user--no-tc-string
  window.addEventListener("FidesUIShown", (event) => {
    const { tc_string: tcString } = event.detail;
    cmpApi.update(tcString ?? null, true);
  });
  // UI is no longer visible
  // see https://github.com/InteractiveAdvertisingBureau/iabtcf-es/tree/master/modules/cmpapi#dont-show-ui--tc-string-does-not-need-an-update
  window.addEventListener("FidesModalClosed", (event) => {
    const { tc_string: tcString } = event.detail;
    cmpApi.update(tcString ?? null, false);
  });
  // User preference collected
  // see https://github.com/InteractiveAdvertisingBureau/iabtcf-es/tree/master/modules/cmpapi#show-ui--tc-string-needs-update
  window.addEventListener("FidesUpdated", (event) => {
    const { tc_string: tcString } = event.detail;
    cmpApi.update(tcString ?? null, false);
  });
};
