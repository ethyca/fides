import { PrivacyExperience, PrivacyExperienceMinimal } from "../consent-types";
import {
  GVLJson,
  TCFVendorConsentRecord,
  TCFVendorLegitimateInterestsRecord,
  TCFVendorRelationships,
  VendorRecord,
} from "./types";

export enum VendorSources {
  GVL = "gvl",
  AC = "gacp",
}

/**
 * Given a vendor id such as `gvl.2`, return {source: "gvl", id: "2"};
 */
export const decodeVendorId = (vendorId: TCFVendorRelationships["id"]) => {
  const split = vendorId.split(".");
  if (split.length === 1) {
    return { source: undefined, id: split[0] };
  }
  return { source: split[0], id: split[1] };
};

/**
 * Returns the associated GVL entry given a vendor ID. If the id is not found,
 * returns `undefined`.
 *
 * @example If an id of `gvl.2` is passed in, return GVL Vendor #2
 * @example If an id of `ac.2` is passed in, return undefined
 * @example If an id of `2` is passed in, return GVL Vendor #2 (for backwards compatibility)
 */
export const vendorGvlEntry = (
  vendorId: TCFVendorRelationships["id"],
  gvl: GVLJson | undefined,
) => {
  if (!gvl) {
    return undefined;
  }
  const { source, id } = decodeVendorId(vendorId);
  // For backwards compatibility, we also allow an undefined source but we should
  // remove this once the backend is fully using its new vendor ID scheme.
  if (source === VendorSources.GVL || source === undefined) {
    return gvl.vendors[id];
  }
  return undefined;
};

export const vendorIsAc = (vendorId: TCFVendorRelationships["id"]) =>
  decodeVendorId(vendorId).source === VendorSources.AC;

export const uniqueGvlVendorIds = (experience: PrivacyExperience): number[] => {
  const { tcf_vendor_relationships: vendors = [] } = experience;

  const gvlIds = vendors
    .map((v) => v.id)
    .filter((uid) => vendorGvlEntry(uid, experience.gvl));
  // Return [2,4] as numbers
  return gvlIds.map((uid) => +decodeVendorId(uid).id);
};

export const uniqueGvlVendorIdsFromMinimal = (
  experienceMinimal: PrivacyExperienceMinimal,
): number[] => {
  const combinedIds = [
    ...(experienceMinimal.tcf_vendor_consent_ids || []),
    ...(experienceMinimal.tcf_vendor_legitimate_interest_ids || []),
  ];
  // creating a set automatically removes duplicates
  const uniqueCombinedSet = new Set(combinedIds);

  const gvlIds = [...uniqueCombinedSet].filter((uid) =>
    vendorGvlEntry(uid, experienceMinimal.gvl),
  );
  // Return [2,4] as numbers
  return gvlIds.map((uid) => +decodeVendorId(uid).id);
};

const transformVendorDataToVendorRecords = ({
  consents,
  legints,
  relationships,
  isFidesSystem,
  gvl,
}: {
  consents: TCFVendorConsentRecord[];
  legints: TCFVendorLegitimateInterestsRecord[];
  relationships: TCFVendorRelationships[];
  isFidesSystem: boolean;
  gvl: PrivacyExperience["gvl"];
}) => {
  const records: VendorRecord[] = [];
  relationships.forEach((relationship) => {
    const vendorConsent = consents.find((v) => v.id === relationship.id);
    const vendorLegint = legints.find((v) => v.id === relationship.id);
    const record: VendorRecord = {
      ...relationship,
      ...vendorConsent,
      ...vendorLegint,
      isFidesSystem,
      isConsent: !!vendorConsent,
      isLegint: !!vendorLegint,
      isGvl: !!vendorGvlEntry(relationship.id, gvl),
    };
    records.push(record);
  });
  return records;
};

export const transformExperienceToVendorRecords = (
  experience: PrivacyExperience,
): VendorRecord[] => {
  const {
    tcf_vendor_consents: consentVendors = [],
    tcf_vendor_legitimate_interests: legintVendors = [],
    tcf_vendor_relationships: vendorRelationships = [],
    tcf_system_consents: consentSystems = [],
    tcf_system_legitimate_interests: legintSystems = [],
    tcf_system_relationships: systemRelationships = [],
  } = experience;

  const vendorRecords = transformVendorDataToVendorRecords({
    consents: consentVendors,
    legints: legintVendors,
    relationships: vendorRelationships,
    isFidesSystem: false,
    gvl: experience.gvl,
  });
  const systemRecords = transformVendorDataToVendorRecords({
    consents: consentSystems,
    legints: legintSystems,
    relationships: systemRelationships,
    isFidesSystem: true,
    gvl: experience.gvl,
  });

  const records = [...vendorRecords, ...systemRecords];

  return records;
};
