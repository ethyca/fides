import { FidesKey } from "../common/fides-types";
import { DataCategory } from "./types";

interface DataCategoryNode {
  value: string;
  label: string;
  description?: string;
  children: DataCategoryNode[];
}
// eslint-disable-next-line import/prefer-default-export
export const transformDataCategoriesToNodes = (
  categories: DataCategory[],
  parentKey?: FidesKey
): DataCategoryNode[] => {
  const keyToCompare = parentKey ?? null;
  const thisLevel = categories.filter(
    (category) => category.parent_key === keyToCompare
  );
  const nodes = thisLevel.map((thisLevelCategory) => {
    const thisLevelKey = thisLevelCategory.fides_key;
    return {
      value: thisLevelCategory.fides_key,
      label: thisLevelCategory.name ?? thisLevelCategory.fides_key,
      description: thisLevelCategory.description,
      children: transformDataCategoriesToNodes(categories, thisLevelKey),
    };
  });
  return nodes;
};
