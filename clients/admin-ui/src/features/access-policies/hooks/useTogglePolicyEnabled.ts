import { useMessage } from "fidesui";
import { useCallback } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { RTKErrorResult } from "~/types/errors/api";

import { useUpdateAccessPolicyMutation } from "../access-policies.slice";
import { updateYamlField } from "../policy-yaml";
import { AccessPolicyListItem } from "../types";

export const useTogglePolicyEnabled = () => {
  const [updatePolicy] = useUpdateAccessPolicyMutation();
  const message = useMessage();

  return useCallback(
    async (policy: AccessPolicyListItem) => {
      if (!policy.yaml) {
        return;
      }
      const updatedYaml = updateYamlField(
        policy.yaml,
        "enabled",
        !policy.enabled,
      );
      try {
        await updatePolicy({ id: policy.id, yaml: updatedYaml }).unwrap();
      } catch (error) {
        message.error(getErrorMessage((error as RTKErrorResult["error"])));
      }
    },
    [updatePolicy, message],
  );
};
