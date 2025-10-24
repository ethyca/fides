import { TaxonomyEntity, TaxonomyEntityNode } from "./types";

export const transformTaxonomyEntityToNodes = (
  entities: TaxonomyEntity[],
  parentKey?: string | null,
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
    };
  });
  return nodes;
};
