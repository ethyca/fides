import { useMemo } from "react";

import { ControlGroup } from "../access-policies.slice";
import { AccessPolicyListItem } from "../types";

export interface PolicyGroup {
  controlGroup: ControlGroup;
  policies: AccessPolicyListItem[];
}

export const useAccessPolicyGroups = (
  policies: AccessPolicyListItem[],
  controlGroups: ControlGroup[] | undefined,
): PolicyGroup[] =>
  useMemo(() => {
    if (!controlGroups) {
      return [];
    }

    const groups: PolicyGroup[] = controlGroups.map((controlGroup) => ({
      controlGroup,
      policies: policies.filter((policy) =>
        policy.controls?.includes(controlGroup.key),
      ),
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

    return groups.filter((g) => g.policies.length > 0);
  }, [policies, controlGroups]);
