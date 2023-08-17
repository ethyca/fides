import { TCFFeatureRecord, TCFPurposeRecord } from "./types";

export interface Stack {
  id: number;
  purposes: number[];
  specialFeatures: number[];
  name: string;
  description: string;
}

export const createStacks = ({
  purposeIds,
  specialFeatureIds,
  stacks,
}: {
  purposeIds: Array<TCFPurposeRecord["id"]>;
  specialFeatureIds: Array<TCFFeatureRecord["id"]>;
  stacks: Record<string, Stack>;
}) => {
  const purposeIdsSet = new Set(purposeIds);
  const specialFeatureIdsSet = new Set(specialFeatureIds);

  const matches = Object.entries(stacks).filter(([, stack]) => {
    // every purpose/special feature in the stack must be covered
    const purposesMatch = stack.purposes.every((p) => purposeIdsSet.has(p));
    const specialFeaturesMatch = stack.specialFeatures.every((sf) =>
      specialFeatureIdsSet.has(sf)
    );
    return purposesMatch && specialFeaturesMatch;
  });

  return matches.map((match) => match[1]);
};
