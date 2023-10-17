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
