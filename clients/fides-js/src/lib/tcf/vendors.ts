import { GVLJson, LegalBasisForProcessingEnum, TCFVendorRecord } from "./types";

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
