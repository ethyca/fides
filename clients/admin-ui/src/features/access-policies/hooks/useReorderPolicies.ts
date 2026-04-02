import { useCallback } from "react";

import { useReorderAccessPolicyMutation } from "../access-policies.slice";
import { AccessPolicyListItem } from "../types";

export const useReorderPolicies = () => {
  const [reorderPolicy] = useReorderAccessPolicyMutation();

  return useCallback(
    (
      policies: AccessPolicyListItem[],
      fromIndex: number,
      toIndex: number,
    ) => {
      const reordered = [...policies];
      const [moved] = reordered.splice(fromIndex, 1);
      reordered.splice(toIndex, 0, moved);

      const insertAfterId = toIndex > 0 ? reordered[toIndex - 1].id : null;
      reorderPolicy({ id: moved.id, insert_after_id: insertAfterId });
    },
    [reorderPolicy],
  );
};
