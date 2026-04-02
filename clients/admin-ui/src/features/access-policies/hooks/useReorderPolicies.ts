import { useMessage } from "fidesui";
import { useCallback } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { RTKErrorResult } from "~/types/errors/api";

import { useReorderAccessPolicyMutation } from "../access-policies.slice";
import { AccessPolicyListItem } from "../types";

export const useReorderPolicies = () => {
  const [reorderPolicy] = useReorderAccessPolicyMutation();
  const message = useMessage();

  return useCallback(
    async (
      policies: AccessPolicyListItem[],
      fromIndex: number,
      toIndex: number,
    ) => {
      const reordered = [...policies];
      const [moved] = reordered.splice(fromIndex, 1);
      reordered.splice(toIndex, 0, moved);

      const insertAfterId = toIndex > 0 ? reordered[toIndex - 1].id : null;
      try {
        await reorderPolicy({ id: moved.id, insert_after_id: insertAfterId }).unwrap();
      } catch (error) {
        message.error(getErrorMessage((error as RTKErrorResult["error"])));
      }
    },
    [reorderPolicy, message],
  );
};
