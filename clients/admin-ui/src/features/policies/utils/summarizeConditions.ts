import { pluralize } from "~/features/common/utils";
import type { ConditionGroup, ConditionLeaf } from "~/types/api";

import { extractLeafConditions } from "./extractLeafConditions";

/**
 * Summarize the conditions for display in the policies list. Currently only supports counting the number of conditions (eg "1 condition" or "3 conditions"). Future implementations may include more detailed summaries like "Locations in Europe" or "Regulations in GDPR".
 */
export const summarizeConditions = (
  conditions: ConditionGroup | ConditionLeaf | null | undefined,
) => {
  const leaves = extractLeafConditions(conditions);
  if (leaves.length === 0) {
    return null;
  }

  return `${leaves.length} ${pluralize(leaves.length, "condition", "conditions")}`;
};
