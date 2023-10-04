import { PrivacyExperience } from "../consent-types";
import {
  GVLJson,
  TCFConsentVendorRecord,
  TCFLegitimateInterestsVendorRecord,
  TCFVendorRelationships,
  VendorRecord,
} from "./types";

export const vendorIsGvl = (
  vendor: Pick<TCFVendorRelationships, "id">,
  gvl: GVLJson | undefined
) => {
  if (!gvl) {
    return undefined;
  }
  return gvl.vendors[vendor.id];
};

const transformVendorDataToVendorRecords = ({
  consents,
  legints,
  relationships,
  isFidesSystem,
}: {
  consents: TCFConsentVendorRecord[];
  legints: TCFLegitimateInterestsVendorRecord[];
  relationships: TCFVendorRelationships[];
  isFidesSystem: boolean;
}) => {
  const records: VendorRecord[] = [];
  relationships.forEach((relationship) => {
    const { id } = relationship;
    const vendorConsent = consents.find((v) => v.id === id);
    const vendorLegint = legints.find((v) => v.id === id);
    const record: VendorRecord = {
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
    tcf_consent_vendors: consentVendors = [],
    tcf_legitimate_interests_vendors: legintVendors = [],
    tcf_vendor_relationships: vendorRelationships = [],
    tcf_consent_systems: consentSystems = [],
    tcf_legitimate_interests_systems: legintSystems = [],
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
