import {
  PurposeRecord,
  TCFPurposeConsentRecord,
  TCFPurposeLegitimateInterestsRecord,
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
    ])
  );
  const purposes: PurposeRecord[] = [];
  uniqueIds.forEach((id) => {
    const consent = consentPurposes.find((p) => p.id === id);
    const legint = legintPurposes.find((p) => p.id === id);
    if (consent) {
      purposes.push({ ...consent, isConsent: true, isLegint: false });
    } else if (legint) {
      purposes.push({ ...legint, isConsent: false, isLegint: true });
    }
  });

  return { uniquePurposeIds: uniqueIds, uniquePurposes: purposes };
};
