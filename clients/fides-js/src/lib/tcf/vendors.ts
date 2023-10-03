import { PrivacyExperience } from "../consent-types";
import {
  GVLJson,
  LegalBasisForProcessingEnum,
  TCFConsentVendorRecord,
  TCFLegitimateInterestsVendorRecord,
  TCFVendorRelationships,
  VendorRecord,
} from "./types";

export const vendorIsGvl = (
  vendor: Pick<TCFVendorRecord, "id">,
  gvl: GVLJson | undefined
) => {
  if (!gvl) {
    return undefined;
  }
  return gvl.vendors[vendor.id];
};

export const vendorRecordsWithLegalBasis = (
  records: TCFVendorRecord[],
  legalBasis: LegalBasisForProcessingEnum
) =>
  records.filter((record) => {
    const { purposes, special_purposes: specialPurposes } = record;
    const hasApplicablePurposes = purposes?.filter((purpose) =>
      purpose.legal_bases?.includes(legalBasis)
    );
    const hasApplicableSpecialPurposes = specialPurposes?.filter((purpose) =>
      purpose.legal_bases?.includes(legalBasis)
    );
    return (
      hasApplicablePurposes?.length || hasApplicableSpecialPurposes?.length
    );
  });

const transformVendorDataToVendorRecords = ({
  consents,
  legints,
  relationships,
  isFidesSystem,
  gvl,
}: {
  consents: TCFConsentVendorRecord[];
  legints: TCFLegitimateInterestsVendorRecord[];
  relationships: TCFVendorRelationships[];
  isFidesSystem: boolean;
  gvl?: GVLJson;
}) => {
  const records: VendorRecord[] = [];
  relationships.forEach((relationship) => {
    const { id } = relationship;
    const vendorConsent = consents.find((v) => v.id === id);
    const vendorLegint = legints.find((v) => v.id === id);
    const record: VendorRecord = {
      ...relationship,
      consent_purposes: vendorConsent?.consent_purposes,
      legitimate_interests_purposes:
        vendorLegint?.legitimate_interests_purposes,
      isFidesSystem,
      isGvl: !!vendorIsGvl(relationship, gvl),
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
    gvl: experience.gvl,
    isFidesSystem: false,
  });
  const systemRecords = transformVendorDataToVendorRecords({
    consents: consentSystems,
    legints: legintSystems,
    relationships: systemRelationships,
    gvl: experience.gvl,
    isFidesSystem: true,
  });

  const records = [...vendorRecords, ...systemRecords];

  return records;
};
