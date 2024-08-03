import { DataCategoryWithConfidence } from "~/features/dataset/types";

/**
 * Determine which data categories to show in the case where we have data categories
 * saved to a resource and recommendations from a classifier.
 */
export const initialDataCategories = ({
  dataCategories,
  mostLikelyCategories,
}: {
  dataCategories?: string[];
  mostLikelyCategories?: DataCategoryWithConfidence[];
}) => {
  if (dataCategories?.length) {
    return dataCategories;
  }

  // If there are classifier suggestions, choose the highest-confidence option.
  if (mostLikelyCategories?.length) {
    const topCategory = mostLikelyCategories.reduce((maxCat, nextCat) =>
      (nextCat.confidence ?? 0) > (maxCat.confidence ?? 0) ? nextCat : maxCat,
    );
    return [topCategory.fides_key];
  }

  return [];
};
