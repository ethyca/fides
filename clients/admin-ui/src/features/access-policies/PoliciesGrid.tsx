import { Empty, Spin } from "fidesui";

import { ControlGroup } from "./access-policies.slice";
import { PolicyGroup } from "./hooks";
import PolicyCategoryGroup from "./PolicyCategoryGroup";
import { AccessPolicyListItem } from "./types";

interface PoliciesGridProps {
  groups: PolicyGroup[];
  controlGroups: ControlGroup[];
  onTogglePolicy: (policy: AccessPolicyListItem) => void;
  isLoading: boolean;
}

const PoliciesGrid = ({
  groups,
  controlGroups,
  onTogglePolicy,
  isLoading,
}: PoliciesGridProps) => {
  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spin size="large" />
      </div>
    );
  }

  if (groups.length === 0) {
    return <Empty description="No policies found" className="py-12" />;
  }

  return (
    <div>
      {groups.map((group) => (
        <PolicyCategoryGroup
          key={group.controlGroup.key}
          controlGroup={group.controlGroup}
          policies={group.policies}
          controlGroups={controlGroups}
          onTogglePolicy={onTogglePolicy}
        />
      ))}
    </div>
  );
};

export default PoliciesGrid;
