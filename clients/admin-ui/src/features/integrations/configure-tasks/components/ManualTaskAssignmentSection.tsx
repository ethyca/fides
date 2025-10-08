import {
  AntFlex as Flex,
  AntSelect as Select,
  AntTypography as Typography,
} from "fidesui";
import { useMemo } from "react";

interface UserOption {
  label: string;
  value: string;
  displayName: string;
}

interface ManualTaskAssignmentSectionProps {
  selectedUsers: string[];
  userOptions: UserOption[];
  onUserAssignmentChange: (userIds: string[]) => void;
}

const ManualTaskAssignmentSection = ({
  selectedUsers,
  userOptions,
  onUserAssignmentChange,
}: ManualTaskAssignmentSectionProps) => {
  // Sort options to show selected users first
  const sortedOptions = useMemo(() => {
    const selected = userOptions.filter((option) =>
      selectedUsers.includes(option.value),
    );
    const unselected = userOptions.filter(
      (option) => !selectedUsers.includes(option.value),
    );
    return [...selected, ...unselected];
  }, [userOptions, selectedUsers]);

  return (
    <div>
      <Flex align="center" gap="middle">
        <Typography.Text strong>Assign manual tasks to users:</Typography.Text>
        <Select
          className="flex-1"
          placeholder="Select users to assign manual tasks to"
          aria-label="Select users to assign manual tasks to"
          mode="multiple"
          maxTagCount="responsive"
          value={selectedUsers}
          onChange={onUserAssignmentChange}
          options={sortedOptions}
          optionLabelProp="displayName"
          tokenSeparators={[","]}
          data-testid="assign-users-select"
          filterOption={(input, option) => {
            return (
              (typeof option?.label === "string" &&
                option.label.toLowerCase().includes(input.toLowerCase())) ||
              false
            );
          }}
        />
      </Flex>
    </div>
  );
};

export default ManualTaskAssignmentSection;
