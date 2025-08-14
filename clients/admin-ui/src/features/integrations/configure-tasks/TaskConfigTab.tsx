import {
  AntButton as Button,
  AntDivider as Divider,
  AntFlex as Flex,
  AntTypography as Typography,
} from "fidesui";

import { ConnectionConfigurationResponse } from "~/types/api";

import ManualTaskAssignmentSection from "./components/ManualTaskAssignmentSection";
import ManualTaskConfigTable from "./components/ManualTaskConfigTable";
import CreateExternalUserModal from "./CreateExternalUserModal";
import { useUserAssignment } from "./hooks/useUserAssignment";

interface TaskConfigTabProps {
  integration: ConnectionConfigurationResponse;
}

const TaskConfigTab = ({ integration }: TaskConfigTabProps) => {
  const {
    selectedUsers,
    userOptions,
    handleUserAssignmentChange,
    handleUserCreated,
    isCreateUserOpen,
    onCreateUserOpen,
    onCreateUserClose,
  } = useUserAssignment({ integration });

  const handleUserCreatedWithRefresh = () => {
    handleUserCreated();
    onCreateUserClose();
  };

  return (
    <div>
      <Flex vertical gap={16}>
        <Typography.Paragraph className="mt-2 w-2/3">
          Configure manual tasks for this integration. Manual tasks allow you to
          define custom data collection or processing steps that require human
          intervention.
        </Typography.Paragraph>

        <ManualTaskConfigTable integration={integration} />
        <Divider className="my-2" />

        <ManualTaskAssignmentSection
          selectedUsers={selectedUsers}
          userOptions={userOptions}
          onUserAssignmentChange={handleUserAssignmentChange}
        />
        <Flex justify="start">
          <Button
            type="default"
            onClick={onCreateUserOpen}
            data-testid="manage-secure-access-btn"
          >
            Create external user
          </Button>
        </Flex>

        <CreateExternalUserModal
          isOpen={isCreateUserOpen}
          onClose={onCreateUserClose}
          onUserCreated={handleUserCreatedWithRefresh}
        />
      </Flex>
    </div>
  );
};

export default TaskConfigTab;
