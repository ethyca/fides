import {
  LegalBasisEnum,
  PurposeRecord,
  TCFPurposeConsentRecord,
  TCFPurposeLegitimateInterestsRecord,
  TCFSpecialPurposeRecord,
} from "./types";

export const getUniquePurposeRecords = ({
  consentPurposes = [],
  legintPurposes = [],
}: {
  consentPurposes: TCFPurposeConsentRecord[] | undefined;
  legintPurposes: TCFPurposeLegitimateInterestsRecord[] | undefined;
}) => {
  const uniqueIds = Array.from(
    new Set([
      ...consentPurposes.map((p) => p.id),
      ...legintPurposes.map((p) => p.id),
    ]),
  ).sort((a, b) => a - b);
  const purposes: PurposeRecord[] = [];
  uniqueIds.forEach((id) => {
    const consent = consentPurposes.find((p) => p.id === id);
    const legint = legintPurposes.find((p) => p.id === id);
    if (consent || legint) {
      const record = { ...consent, ...legint } as
        | TCFPurposeConsentRecord
        | TCFPurposeLegitimateInterestsRecord;
      purposes.push({
        ...record,
        id,
        isConsent: !!consent,
        isLegint: !!legint,
      });
    }
  });

  return { uniquePurposeIds: uniqueIds, uniquePurposes: purposes };
};

/**
 * Returns whether or not a special purpose has a specificed LegalBasisEnum
 */
export const hasLegalBasis = (
  specialPurpose: TCFSpecialPurposeRecord,
  legalBasis: LegalBasisEnum,
) => {
  const { legal_bases: legalBases } = specialPurpose;
  if (!legalBases) {
    return false;
  }
  // NOTE: In Typescript 4.9.5 you can't implicitly coerce string enums like
  // LegalBasisEnum to a string value, so we do an explicit conversion here
  return !!legalBases.find((basis) => basis === legalBasis.toString());
};
