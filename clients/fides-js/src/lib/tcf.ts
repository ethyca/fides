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
import { EnabledIds, TcfPublisherRestriction } from "./tcf/types";
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
const AC_SPECIFICATION_VERSION = 2;

/**
 * Generates an Additional Consent (AC) string in the format `version~id1.id2.id3~id4.id5.id6` where:
 * - version: The AC specification version
 * - id1.id2.id3: A sorted, dot-separated list of user-consented vendor IDs.
 * - id4.id5.id6: "dv." followed by a sorted, dot-separated list of non-user-consented disclosed
 *  vendor IDs.
 *
 * Vendors included in the user-consented list should not be included in the disclosed vendor list
 * to reduce the string size.
 *
 * The function filters for AC vendors only (those with 'gacp' prefix), extracts their numeric IDs,
 * and joins them in ascending order.
 *
 * @example
 * generateAcString({
 *   userConsentedVendorIds: ["gacp.42"],
 *   disclosedVendorIds: ["gacp.49", "gacp.33", "gvl.12", "gacp.42", "gvl.123"]
 * })
 * // Returns "2~42~dv.33.49"
 */
const generateAcString = ({
  userConsentedVendorIds,
  disclosedVendorIds,
}: {
  userConsentedVendorIds: string[];
  disclosedVendorIds: string[];
}) => {
  const processIds = (ids: string[]) =>
    ids
      .filter(vendorIsAc)
      .map((id) => decodeVendorId(id).id)
      .sort((a, b) => Number(a) - Number(b))
      .join(".");

  const consentedIds = processIds(userConsentedVendorIds);
  const disclosedIds = processIds(
    disclosedVendorIds.filter((id) => !userConsentedVendorIds.includes(id)),
  );

  return `${AC_SPECIFICATION_VERSION}~${consentedIds}~dv.${disclosedIds}`;
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

    if (experience.tcf_publisher_country_code) {
      tcModel.publisherCountryCode = experience.tcf_publisher_country_code;
    }
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

          if (!experience.tcf_publisher_restrictions?.length) {
            // Legacy: look up each vendor in the GVL vendors list to see if they have a purpose list.
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

      // Set legitimate interest for special-purpose only vendors and vendors that
      // have declared only purposes based on consent (no LI) + at least one SP
      if (experience.gvl?.vendors) {
        (experience as PrivacyExperience).tcf_vendor_relationships?.forEach(
          (relationship) => {
            const { id } = decodeVendorId(relationship.id);
            const vendor = experience.gvl?.vendors[id];
            if (
              vendor &&
              vendor.specialPurposes?.length &&
              (!vendor.legIntPurposes || vendor.legIntPurposes.length === 0)
            ) {
              tcModel.vendorLegitimateInterests.set(+id);
            }
          },
        );
      }

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

      // Process publisher restrictions if available
      if (
        experience.tcf_publisher_restrictions &&
        experience.tcf_publisher_restrictions.length > 0
      ) {
        experience.tcf_publisher_restrictions.forEach(
          (restriction: TcfPublisherRestriction) => {
            // NOTE: While this documentation https://github.com/InteractiveAdvertisingBureau/GDPR-Transparency-and-Consent-Framework/blob/master/TCFv2/TCF-Implementation-Guidelines.md#pubrestrenc
            // mentions "it might be more efficient to encode a small number of range restriction
            // segments using a specific encoding scheme," this is referring to the CMP's interface (Admin UI)
            // providing a mechanism for handling ranges, but the TCModel.publisherRestrictions object does
            // not support ranges. We must add each vendor id as a separate publisher restriction because
            // that's what the TCModel we're using for our encoding supports.
            // See https://github.com/InteractiveAdvertisingBureau/iabtcf-es/tree/master/modules/core#setting-publisher-restrictions
            // for more information about the loop below.
            restriction.vendors.forEach((vendorId: number) => {
              const purposeRestriction = new PurposeRestriction();
              purposeRestriction.purposeId = restriction.purpose_id;
              purposeRestriction.restrictionType = restriction.restriction_type;
              tcModel.publisherRestrictions.add(vendorId, purposeRestriction);
            });
          },
        );
      }

      encodedString = TCString.encode(tcModel, {
        // We do not want to include vendors disclosed or publisher tc at the moment
        segments: [Segment.CORE],
      });

      fidesDebugger(
        "TC String encoded",
        `https://iabgpp.com/#${encodedString}`,
      );

      // Attach the AC string, which only applies to tcf_vendor_consents (no LI exists in AC)
      const disclosedVendorIds = experience.minimal_tcf
        ? (experience as PrivacyExperienceMinimal).tcf_vendor_consent_ids
        : (experience as PrivacyExperience).tcf_vendor_consents?.map(
            (vendor) => vendor.id,
          );
      const acString = generateAcString({
        userConsentedVendorIds: tcStringPreferences?.vendorsConsent ?? [],
        disclosedVendorIds: disclosedVendorIds ?? [],
      });
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

  // For rules around when to update the TC string, see
  // https://github.com/InteractiveAdvertisingBureau/GDPR-Transparency-and-Consent-Framework/blob/master/TCFv2/IAB%20Tech%20Lab%20-%20CMP%20API%20v2.md#addeventlistener

  // Initialize api with TC string. We only want to *update*
  // the TC string if all of the following are true:
  //   1. TC string was _already set_ on a prior visit.
  //   2. We are _not_ going to show the banner (i.e. the TCF hash has not changed).
  //   3. It is the _first_ init (This should only ever happen once per visit).
  // see https://github.com/InteractiveAdvertisingBureau/iabtcf-es/tree/master/modules/cmpapi#dont-show-ui--tc-string-does-not-need-an-update
  window.addEventListener("FidesInitialized", (event) => {
    const tcString = extractTCStringForCmpApi(event);
    if (
      !!tcString &&
      !!event.detail.extraDetails &&
      !event.detail.extraDetails.shouldShowExperience &&
      event.detail.extraDetails.firstInit
    ) {
      // we are not showing the experience, so we use false
      cmpApi.update(tcString, false);
    }
  });
  // UI is visible
  // see https://github.com/InteractiveAdvertisingBureau/iabtcf-es/tree/master/modules/cmpapi#show-ui--tc-string-needs-update
  // and https://github.com/InteractiveAdvertisingBureau/iabtcf-es/tree/master/modules/cmpapi#show-ui--new-user--no-tc-string
  window.addEventListener("FidesUIShown", (event) => {
    const tcString = extractTCStringForCmpApi(event);
    cmpApi.update(tcString, true);
  });

  // User preference collected
  // see https://github.com/InteractiveAdvertisingBureau/iabtcf-es/tree/master/modules/cmpapi#show-ui--tc-string-needs-update
  window.addEventListener("FidesUpdated", (event) => {
    const tcString = extractTCStringForCmpApi(event);
    cmpApi.update(tcString, false);
  });
};
