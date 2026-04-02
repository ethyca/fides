import { useMemo } from "react";

import {
  AccessPolicy,
  ControlGroup,
  useGetAccessPoliciesQuery,
  useUpdateAccessPolicyMutation,
} from "../access-policies.slice";
import { extractPolicyFields, updateYamlField } from "../policy-yaml";
import { AccessPolicyListItem } from "../types";

export { usePoliciesFilters } from "./usePoliciesFilters";

/**
 * Enrich an AccessPolicy with fields parsed from its YAML.
 */
const toListItem = (policy: AccessPolicy): AccessPolicyListItem => {
  const { enabled, priority, decision } = extractPolicyFields(policy.yaml);
  return { ...policy, enabled, priority, decision };
};

/**
 * Fetches all access policies and enriches them with YAML-derived fields,
 * sorted by priority ascending.
 */
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

export interface PolicyGroup {
  controlGroup: ControlGroup;
  policies: AccessPolicyListItem[];
}

/**
 * Groups policies by their control group memberships.
 * A policy with multiple controls appears in each group.
 * Policies with no controls go under an "Ungrouped" entry.
 */
export const useAccessPolicyGroups = (
  policies: AccessPolicyListItem[],
  controlGroups: ControlGroup[] | undefined,
): PolicyGroup[] =>
  useMemo(() => {
    if (!controlGroups) {
      return [];
    }

    const groups: PolicyGroup[] = controlGroups.map((cg) => ({
      controlGroup: cg,
      policies: policies.filter((p) => p.controls?.includes(cg.key)),
    }));

    const ungrouped = policies.filter(
      (p) => !p.controls || p.controls.length === 0,
    );
    if (ungrouped.length > 0) {
      groups.push({
        controlGroup: { key: "_ungrouped", label: "Ungrouped" },
        policies: ungrouped,
      });
    }

    // Only return groups that have at least one policy
    return groups.filter((g) => g.policies.length > 0);
  }, [policies, controlGroups]);

/**
 * Returns a callback to toggle a policy's `enabled` field in its YAML
 * and persist via the update mutation.
 */
export const useTogglePolicyEnabled = () => {
  const [updatePolicy] = useUpdateAccessPolicyMutation();

  return (policy: AccessPolicyListItem) => {
    if (!policy.yaml) {
      return;
    }
    const updatedYaml = updateYamlField(
      policy.yaml,
      "enabled",
      !policy.enabled,
    );
    updatePolicy({ id: policy.id, yaml: updatedYaml });
  };
};

/**
 * Returns a callback to directly set a policy's priority value in its YAML.
 */
export const useUpdatePolicyPriority = () => {
  const [updatePolicy] = useUpdateAccessPolicyMutation();

  return (policy: AccessPolicyListItem, newPriority: number) => {
    if (!policy.yaml) {
      return;
    }
    const updatedYaml = updateYamlField(policy.yaml, "priority", newPriority);
    updatePolicy({ id: policy.id, yaml: updatedYaml });
  };
};

/**
 * Returns a callback that reorders policies by updating their priority
 * values in the YAML. Assigns sequential priorities (100, 200, 300, ...)
 * after the move.
 */
export const useReorderPolicies = () => {
  const [updatePolicy] = useUpdateAccessPolicyMutation();

  return (
    policies: AccessPolicyListItem[],
    fromIndex: number,
    toIndex: number,
  ) => {
    const reordered = [...policies];
    const [moved] = reordered.splice(fromIndex, 1);
    reordered.splice(toIndex, 0, moved);

    // Reassign sequential priorities and update any that changed
    reordered.forEach((policy, idx) => {
      const newPriority = (idx + 1) * 100;
      if (policy.priority !== newPriority && policy.yaml) {
        const updatedYaml = updateYamlField(
          policy.yaml,
          "priority",
          newPriority,
        );
        updatePolicy({ id: policy.id, yaml: updatedYaml });
      }
    });
  };
};
