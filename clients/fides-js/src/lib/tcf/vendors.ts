import { PrivacyExperience } from "../consent-types";
import {
  GVLJson,
  TCFVendorConsentRecord,
  TCFVendorLegitimateInterestsRecord,
  TCFVendorRelationships,
  VendorRecord,
} from "./types";

enum VendorSouces {
  GVL = "gvl",
  AC = "ac",
}

export const vendorIsGvl = (
  vendor: Pick<TCFVendorRelationships, "id">,
  gvl: GVLJson | undefined
) => {
  if (!gvl) {
    return undefined;
  }
  return gvl.vendors[vendor.id];
};

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

export const vendorIsAc = (vendorId: TCFVendorRelationships["id"]) =>
  decodeVendorId(vendorId).source === VendorSouces.AC;

const transformVendorDataToVendorRecords = ({
  consents,
  legints,
  relationships,
  isFidesSystem,
}: {
  consents: TCFVendorConsentRecord[];
  legints: TCFVendorLegitimateInterestsRecord[];
  relationships: TCFVendorRelationships[];
  isFidesSystem: boolean;
}) => {
  const records: VendorRecord[] = [];
  const uniqueVendorIds = Array.from(
    new Set([...consents.map((c) => c.id), ...legints.map((l) => l.id)])
  );
  uniqueVendorIds.forEach((id) => {
    const vendorConsent = consents.find((v) => v.id === id);
    const vendorLegint = legints.find((v) => v.id === id);
    const relationship = relationships.find((r) => r.id === id);
    const record: VendorRecord = {
      id,
      ...relationship,
      ...vendorConsent,
      ...vendorLegint,
      isFidesSystem,
      isConsent: !!vendorConsent,
      isLegint: !!vendorLegint,
    };
    records.push(record);
  });
  return records;
};

export const transformExperienceToVendorRecords = (
  experience: PrivacyExperience
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
  });
  const systemRecords = transformVendorDataToVendorRecords({
    consents: consentSystems,
    legints: legintSystems,
    relationships: systemRelationships,
    isFidesSystem: true,
  });

  const records = [...vendorRecords, ...systemRecords];

  return records;
};
