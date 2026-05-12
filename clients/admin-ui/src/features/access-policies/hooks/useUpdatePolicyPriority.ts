import { useMessage } from "fidesui";
import { useCallback } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { RTKErrorResult } from "~/types/errors/api";

import { useUpdateAccessPolicyMutation } from "../access-policies.slice";
import { updateYamlField } from "../policy-yaml";
import { AccessPolicyListItem } from "../types";

export const useUpdatePolicyPriority = () => {
  const [updatePolicy] = useUpdateAccessPolicyMutation();
  const message = useMessage();

  return useCallback(
    async (policy: AccessPolicyListItem, newPriority: number) => {
      if (!policy.yaml) {
        message.warning("Policy YAML is unavailable — cannot update.");
        return;
      }
      const updatedYaml = updateYamlField(policy.yaml, "priority", newPriority);
      try {
        await updatePolicy({ id: policy.id, yaml: updatedYaml }).unwrap();
      } catch (error) {
        message.error(getErrorMessage(error as RTKErrorResult["error"]));
      }
    },
    [updatePolicy, message],
  );
};
