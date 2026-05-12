import { useMemo } from "react";

import {
  AccessPolicy,
  useGetAccessPoliciesQuery,
} from "../access-policies.slice";
import { extractPolicyFields } from "../policy-yaml";
import { AccessPolicyListItem } from "../types";

const toListItem = (policy: AccessPolicy): AccessPolicyListItem => {
  const { enabled, priority, decision } = extractPolicyFields(policy.yaml);
  return { ...policy, enabled, priority, decision };
};

export const useAccessPoliciesList = () => {
  const { data, isLoading, isError } = useGetAccessPoliciesQuery({});

  const policies = useMemo(() => {
    if (!data?.items) {
      return [];
    }
    return data.items.map(toListItem).sort((a, b) => a.priority - b.priority);
  }, [data]);

  return { policies, isLoading, isError };
};
