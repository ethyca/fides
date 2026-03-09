import type { ConditionGroup, ConditionLeaf } from "~/types/api";

export const extractLeafConditions = (
  conditions: ConditionGroup | ConditionLeaf | null | undefined,
): ConditionLeaf[] => {
  if (!conditions) {
    return [];
  }

  if ("field_address" in conditions) {
    return [conditions];
  }

  return conditions.conditions.flatMap((child) => extractLeafConditions(child));
};
