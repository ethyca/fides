import { TCFFeatureRecord, TCFPurposeConsentRecord } from "./types";

export interface Stack {
  id: number;
  purposes: number[];
  specialFeatures: number[];
  name: string;
  description: string;
}

/**
 * Figure out the stacks that match based on a list of purpose and special feature IDs.
 * Filter only to the matches that have the highest overlap with the given lists.
 *
 * Examples:
 * If we have stack definitions
 * 1. [1,2,3]
 * 2. [4,5,6]
 * 3. [1,2,3,4]
 *
 * For the following purposes, we would return:
 * Purposes: [1,2,3] --> Stack 1
 * Purposes: [3,4,5,6] --> Stack 2
 * Purposes: [1,2,3,4,5,6,7] --> Stacks 2 and 3
 */
export const createStacks = ({
  purposeIds,
  specialFeatureIds,
  stacks,
}: {
  purposeIds: Array<TCFPurposeConsentRecord["id"]>;
  specialFeatureIds: Array<TCFFeatureRecord["id"]>;
  stacks: Record<string, Stack>;
}) => {
  const purposeIdsSet = new Set(purposeIds);
  const specialFeatureIdsSet = new Set(specialFeatureIds);

  const matches = Object.entries(stacks).filter(([, stack]) => {
    // every purpose/special feature in the stack must be covered
    const purposesMatch = stack.purposes.every((p) => purposeIdsSet.has(p));
    const specialFeaturesMatch = stack.specialFeatures.every((sf) =>
      specialFeatureIdsSet.has(sf),
    );
    return purposesMatch && specialFeaturesMatch;
  });

  const matchingStacks = matches.map((match) => match[1]);
  // Compare all matches to find the matches that contain the most ids.
  // If a stack with purposes [1,2] and another with purposes [1,2,3] both match,
  // we only want to return [1,2,3].
  return matchingStacks.filter((match1) => {
    const purposes1 = match1.purposes;
    const features1 = match1.specialFeatures;
    const purposeSubsets = matchingStacks.filter((match2) => {
      const purposes2 = new Set(match2.purposes);
      return purposes1.every((p) => purposes2.has(p));
    });
    const featureSubsets = matchingStacks.filter((match2) => {
      const features2 = new Set(match2.specialFeatures);
      return features1.every((f) => features2.has(f));
    });

    if (purposes1.length && purposeSubsets.length === 1) {
      return true;
    }

    if (features1.length && featureSubsets.length === 1) {
      return true;
    }
    // Note: As of 8/21/23, there are no stacks that have both purposes and special features.
    // If a stack one day does feature both, then we'd need to add logic here to
    // decide how to deal with matches, as well as conflicts in matches (for example,
    // if one stack has more matching purposes but another has more matching special features)
    return false;
  });
};

export const getIdsNotRepresentedInStacks = ({
  ids,
  stacks,
  modelType,
}: {
  ids: number[];
  stacks: Stack[];
  modelType: "purposes" | "specialFeatures";
}) => {
  const idsInStacks = new Set(
    ([] as number[]).concat(...stacks.map((s) => s[modelType])),
  );
  return ids.filter((id) => !idsInStacks.has(id));
};
