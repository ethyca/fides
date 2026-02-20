import { pluralize } from "~/features/common/utils";
import { ConditionGroup, ConditionLeaf } from "~/types/api";

const countConditionLeaves = (node: ConditionGroup | ConditionLeaf): number => {
  if ("conditions" in node) {
    return node.conditions.reduce(
      (sum, child) => sum + countConditionLeaves(child),
      0,
    );
  }
  return 1;
};

/**
 * Summarize the conditions for display in the policies list. Currently only supports counting the number of conditions (eg "1 condition" or "3 conditions"). Future implementations may include more detailed summaries like "Locations in Europe" or "Regulations in GDPR".
 * @param conditions - The condition group or leaf to summarize.
 * @returns The summarized conditions.
 */
export const summarizeConditions = (
  conditions: ConditionGroup | ConditionLeaf | null | undefined,
) => {
  if (!conditions) {
    return null;
  }
  const numberOfConditions = countConditionLeaves(conditions);

  return `${numberOfConditions} ${pluralize(numberOfConditions, "condition", "conditions")}`;
};
