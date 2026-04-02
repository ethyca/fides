import { useCallback } from "react";

import { useUpdateAccessPolicyMutation } from "../access-policies.slice";
import { updateYamlField } from "../policy-yaml";
import { AccessPolicyListItem } from "../types";

export const useUpdatePolicyPriority = () => {
  const [updatePolicy] = useUpdateAccessPolicyMutation();

  return useCallback(
    (policy: AccessPolicyListItem, newPriority: number) => {
      if (!policy.yaml) {
        return;
      }
      const updatedYaml = updateYamlField(policy.yaml, "priority", newPriority);
      updatePolicy({ id: policy.id, yaml: updatedYaml });
    },
    [updatePolicy],
  );
};
