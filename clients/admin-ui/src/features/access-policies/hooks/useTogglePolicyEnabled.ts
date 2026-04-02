import { useCallback } from "react";

import { useUpdateAccessPolicyMutation } from "../access-policies.slice";
import { updateYamlField } from "../policy-yaml";
import { AccessPolicyListItem } from "../types";

export const useTogglePolicyEnabled = () => {
  const [updatePolicy] = useUpdateAccessPolicyMutation();

  return useCallback(
    (policy: AccessPolicyListItem) => {
      if (!policy.yaml) {
        return;
      }
      const updatedYaml = updateYamlField(
        policy.yaml,
        "enabled",
        !policy.enabled,
      );
      updatePolicy({ id: policy.id, yaml: updatedYaml });
    },
    [updatePolicy],
  );
};
