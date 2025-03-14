/**
 * This file is responsible for all TCF specific logic. It does not get bundled in with
 * vanilla fides-js, since all of its actions are very TCF specific.
 *
 * In the future, this should hold interactions with the CMP API as well as string generation.
 */

import { CmpApi, TCData } from "@iabtechlabtcf/cmpapi";
import {
  GVL,
  PurposeRestriction,
  RestrictionType,
  Segment,
  TCModel,
  TCString,
} from "@iabtechlabtcf/core";

import { PrivacyExperience, PrivacyExperienceMinimal } from "./consent-types";
import { ETHYCA_CMP_ID, FIDES_SEPARATOR } from "./tcf/constants";
import { extractTCStringForCmpApi } from "./tcf/events";
import { EnabledIds } from "./tcf/types";
import {
  decodeVendorId,
  uniqueGvlVendorIds,
  uniqueGvlVendorIdsFromMinimal,
  vendorGvlEntry,
  vendorIsAc,
} from "./tcf/vendors";

// TCF
const CMP_VERSION = 1;
const FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS = [1, 3, 4, 5, 6];

// AC
const AC_SPECIFICATION_VERSION = 1;

/**
 * Generates an Additional Consent (AC) string in the format `version~id1.id2.id3` where:
 * - version: The AC specification version (currently 1)
 * - id1.id2.id3: A sorted, dot-separated list of vendor IDs that have consent
 *
 * The function combines vendors from both consent and legitimate interest lists,
 * filters for AC vendors only (those with 'gacp' prefix), extracts their numeric IDs,
 * and joins them in ascending order.
 *
 * @example
 * // Given vendors ["gacp.42", "gacp.33", "gvl.12", "gacp.49"]
 * generateAcString({tcStringPreferences: {
 *   vendorsConsent: ["gacp.42"],
 *   vendorsLegint: ["gacp.33", "gvl.12", "gacp.49"]
 * }})
 * // Returns "1~33.42.49"
 */
const generateAcString = ({
  tcStringPreferences,
}: {
  tcStringPreferences: Pick<EnabledIds, "vendorsConsent" | "vendorsLegint">;
}) => {
  const vendorIds = [
    ...tcStringPreferences.vendorsConsent,
    ...tcStringPreferences.vendorsLegint,
  ]
    .filter(vendorIsAc)
    .map((id) => decodeVendorId(id).id)
    .sort((a, b) => Number(a) - Number(b))
    .join(".");
  return `${AC_SPECIFICATION_VERSION}~${vendorIds}`;
};

/**
 * Generate FidesString based on TCF and AC-related info from privacy experience.
 * Called when there is either a FidesInitialized or FidesUpdated event
 */
export const generateFidesString = async ({
  experience,
  tcStringPreferences,
}: {
  tcStringPreferences?: EnabledIds;
  experience: PrivacyExperience | PrivacyExperienceMinimal;
}): Promise<string> => {
  let encodedString = "";
  try {
    const tcModel = new TCModel(new GVL(experience.gvl));

    // Some fields will not be populated until a GVL is loaded
    await tcModel.gvl.readyPromise;

    tcModel.cmpId = ETHYCA_CMP_ID;
    tcModel.cmpVersion = CMP_VERSION;
    tcModel.consentScreen = 1; // On which 'screen' consent was captured; this is a CMP proprietary number encoded into the TC string
    tcModel.isServiceSpecific = true;
    tcModel.supportOOB = false;

    // Narrow the GVL to say we've only showed these vendors provided by our experience
    const gvlUID = experience.minimal_tcf
      ? uniqueGvlVendorIdsFromMinimal(experience as PrivacyExperienceMinimal)
      : uniqueGvlVendorIds(experience as PrivacyExperience);
    tcModel.gvl.narrowVendorsTo(gvlUID);

    if (tcStringPreferences) {
      // Set vendors on tcModel
      tcStringPreferences.vendorsConsent.forEach((vendorId) => {
        if (vendorGvlEntry(vendorId, experience.gvl)) {
          const { id } = decodeVendorId(vendorId);
          tcModel.vendorConsents.set(+id);

          // look up each vendor in the GVL vendors list to see if they have a purpose list.
          // If they do not it means they have been set in Admin UI as Vendor Overrides to
          // require consent. In that case we need to set a publisher restriction for the
          // vendor's flexible purposes.
          const vendor = experience.gvl?.vendors[id];
          if (vendor && !vendor?.purposes?.length) {
            vendor.flexiblePurposes.forEach((purpose) => {
              const purposeRestriction = new PurposeRestriction();
              purposeRestriction.purposeId = purpose;
              purposeRestriction.restrictionType =
                RestrictionType.REQUIRE_CONSENT;
              tcModel.publisherRestrictions.add(+id, purposeRestriction);
            });
          }
        }
      });
      tcStringPreferences.vendorsLegint.forEach((vendorId) => {
        if (experience.minimal_tcf) {
          (
            experience as PrivacyExperienceMinimal
          ).tcf_vendor_legitimate_interest_ids?.forEach((vlid) => {
            const { id } = decodeVendorId(vlid);
            tcModel.vendorLegitimateInterests.set(+id);
          });
        } else if (vendorGvlEntry(vendorId, experience.gvl)) {
          const thisVendor = (
            experience as PrivacyExperience
          ).tcf_vendor_legitimate_interests?.filter(
            (v) => v.id === vendorId,
          )[0];

          const vendorPurposes = thisVendor?.purpose_legitimate_interests;
          // Handle the case where a vendor has forbidden legint purposes set
          let skipSetLegInt = false;
          if (vendorPurposes) {
            const legIntPurposeIds = vendorPurposes.map((p) => p.id);
            if (
              legIntPurposeIds.filter((id) =>
                FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS.includes(id),
              ).length
            ) {
              skipSetLegInt = true;
            }
            if (!skipSetLegInt) {
              const { id } = decodeVendorId(vendorId);
              tcModel.vendorLegitimateInterests.set(+id);
            }
          }
        }
      });

      // Set purposes on tcModel
      tcStringPreferences.purposesConsent.forEach((purposeId) => {
        tcModel.purposeConsents.set(+purposeId);
      });
      tcStringPreferences.purposesLegint.forEach((purposeId) => {
        const id = +purposeId;
        if (!FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS.includes(id)) {
          tcModel.purposeLegitimateInterests.set(id);
        }
      });

      // Set special feature opt-ins on tcModel
      tcStringPreferences.specialFeatures.forEach((id) => {
        tcModel.specialFeatureOptins.set(+id);
      });

      // note that we cannot set consent for special purposes nor features because the IAB policy states
      // the user is not given choice by a CMP.
      // See https://iabeurope.eu/iab-europe-transparency-consent-framework-policies/
      // and https://github.com/InteractiveAdvertisingBureau/iabtcf-es/issues/63#issuecomment-581798996
      encodedString = TCString.encode(tcModel, {
        // We do not want to include vendors disclosed or publisher tc at the moment
        segments: [Segment.CORE],
      });

      // Attach the AC string
      const acString = generateAcString({ tcStringPreferences });
      encodedString = `${encodedString}${FIDES_SEPARATOR}${acString}`;

      // GPP string portion is handled by the GPP extension
    }
  } catch (e) {
    // eslint-disable-next-line no-console
    console.error("Unable to instantiate GVL: ", e);
    return Promise.resolve("");
  }
  return Promise.resolve(encodedString);
};

/**
 * Initializes the CMP API, including setting up listeners on FidesEvents to update
 * the CMP API accordingly.
 */
export const initializeTcfCmpApi = () => {
  const isServiceSpecific = true;
  const cmpApi = new CmpApi(ETHYCA_CMP_ID, CMP_VERSION, isServiceSpecific, {
    // Add custom command to support adding `addtlConsent` per AC spec
    getTCData: (next, tcData: TCData, status) => {
      /*
       * If using with 'removeEventListener' command, add a check to see if tcData is not a boolean. */
      if (typeof tcData !== "boolean") {
        const stringSplit = window.Fides.fides_string?.split(FIDES_SEPARATOR);
        const addtlConsent = stringSplit?.length === 2 ? stringSplit[1] : "";
        next({ ...tcData, addtlConsent }, status);
        return;
      }

      // pass data and status along
      next(tcData, status);
    },
  });

  // Initialize api with TC str, we don't yet show UI, so we use false
  // see https://github.com/InteractiveAdvertisingBureau/iabtcf-es/tree/master/modules/cmpapi#dont-show-ui--tc-string-does-not-need-an-update
  window.addEventListener("FidesInitialized", (event) => {
    const tcString = extractTCStringForCmpApi(event);
    cmpApi.update(tcString, false);
  });
  // UI is visible
  // see https://github.com/InteractiveAdvertisingBureau/iabtcf-es/tree/master/modules/cmpapi#show-ui--tc-string-needs-update
  // and https://github.com/InteractiveAdvertisingBureau/iabtcf-es/tree/master/modules/cmpapi#show-ui--new-user--no-tc-string
  window.addEventListener("FidesUIShown", (event) => {
    const tcString = extractTCStringForCmpApi(event);
    cmpApi.update(tcString, true);
  });
  // UI is no longer visible
  // see https://github.com/InteractiveAdvertisingBureau/iabtcf-es/tree/master/modules/cmpapi#dont-show-ui--tc-string-does-not-need-an-update
  window.addEventListener("FidesModalClosed", (event) => {
    const tcString = extractTCStringForCmpApi(event);
    cmpApi.update(tcString, false);
  });
  // User preference collected
  // see https://github.com/InteractiveAdvertisingBureau/iabtcf-es/tree/master/modules/cmpapi#show-ui--tc-string-needs-update
  window.addEventListener("FidesUpdated", (event) => {
    const tcString = extractTCStringForCmpApi(event);
    cmpApi.update(tcString, false);
  });
};
