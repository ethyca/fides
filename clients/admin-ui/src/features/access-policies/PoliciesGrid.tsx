import { Empty, Flex, Spin } from "fidesui";

import { PolicyGroup } from "./hooks/useAccessPolicyGroups";
import PolicyCategoryGroup from "./PolicyCategoryGroup";
import { AccessPolicyListItem } from "./types";

interface PoliciesGridProps {
  groups: PolicyGroup[];
  onTogglePolicy: (policy: AccessPolicyListItem) => void;
  isLoading: boolean;
}

const PoliciesGrid = ({
  groups,
  onTogglePolicy,
  isLoading,
}: PoliciesGridProps) => {
  if (isLoading) {
    return (
      <Flex justify="center" className="py-12">
        <Spin size="large" />
      </Flex>
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
          onTogglePolicy={onTogglePolicy}
        />
      ))}
    </div>
  );
};

export default PoliciesGrid;
