import {
  AntFlex as Flex,
  AntSelect as Select,
  AntTypography as Typography,
} from "fidesui";

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
  return (
    <div>
      <Flex align="center" gap={16}>
        <Typography.Text strong>Assign manual tasks to users:</Typography.Text>
        <Select
          className="flex-1"
          placeholder="Select users to assign manual tasks to"
          mode="multiple"
          maxTagCount="responsive"
          value={selectedUsers}
          onChange={onUserAssignmentChange}
          options={userOptions}
          optionLabelProp="displayName"
          tokenSeparators={[","]}
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
