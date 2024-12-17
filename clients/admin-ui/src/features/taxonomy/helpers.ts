import { ResourceTypes } from "~/types/api";

import { CoreTaxonomiesEnum } from "./constants";
import { TaxonomyEntity, TaxonomyEntityNode } from "./types";

export const transformTaxonomyEntityToNodes = (
  entities: TaxonomyEntity[],
  parentKey?: string,
): TaxonomyEntityNode[] => {
  let thisLevel: TaxonomyEntity[];
  // handle the case where there are no parent keys, i.e. should just be a flat list (data subjects)
  if (
    parentKey == null &&
    entities.every((entity) => entity.parent_key === undefined)
  ) {
    thisLevel = entities;
  } else {
    // handle the case where we have a nested tree structure
    const keyToCompare = parentKey ?? null;
    thisLevel = entities.filter((entity) => entity.parent_key === keyToCompare);
  }
  const nodes = thisLevel.map((thisLevelEntity) => {
    const thisLevelKey = thisLevelEntity.fides_key;
    return {
      value: thisLevelEntity.fides_key,
      label:
        thisLevelEntity.name === "" || thisLevelEntity.name == null
          ? thisLevelEntity.fides_key
          : thisLevelEntity.name,
      description: thisLevelEntity.description,
      children: transformTaxonomyEntityToNodes(entities, thisLevelKey),
      is_default: thisLevelEntity.is_default ?? false,
      active: thisLevelEntity.active ?? false,
    };
  });
  return nodes;
};

export const parentKeyFromFidesKey = (fidesKey: string) => {
  const split = fidesKey.split(".");
  if (split.length === 1) {
    return "";
  }
  return split.slice(0, split.length - 1).join(".");
};

export const taxonomyTypeToResourceType = (
  taxonomyType: CoreTaxonomiesEnum,
) => {
  switch (taxonomyType) {
    case CoreTaxonomiesEnum.DATA_CATEGORIES:
      return ResourceTypes.DATA_CATEGORY;
    case CoreTaxonomiesEnum.DATA_SUBJECTS:
      return ResourceTypes.DATA_SUBJECT;
    case CoreTaxonomiesEnum.DATA_USES:
      return ResourceTypes.DATA_USE;

    default:
      return undefined;
  }
};
