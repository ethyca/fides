import {
  AntButton as Button,
  AntDivider as Divider,
  AntFlex as Flex,
  AntTypography as Typography,
} from "fidesui";
import { useState } from "react";

import { ConnectionConfigurationResponse } from "~/types/api";

import ManualTaskAssignmentSection from "./components/ManualTaskAssignmentSection";
import ManualTaskConfigTable from "./components/ManualTaskConfigTable";
import CreateExternalUserModal from "./CreateExternalUserModal";
import { useUserAssignment } from "./hooks/useUserAssignment";

interface TaskConfigTabProps {
  integration: ConnectionConfigurationResponse;
}

const TaskConfigTab = ({ integration }: TaskConfigTabProps) => {
  const [shouldOpenAddModal, setShouldOpenAddModal] = useState(false);

  const {
    selectedUsers,
    userOptions,
    handleUserAssignmentChange,
    handleUserCreated,
    isCreateUserOpen,
    onCreateUserOpen,
    onCreateUserClose,
  } = useUserAssignment({ integration });

  const handleAddManualTask = () => {
    setShouldOpenAddModal(true);
  };

  const handleAddModalOpenComplete = () => {
    setShouldOpenAddModal(false);
  };

  const handleUserCreatedWithRefresh = () => {
    handleUserCreated();
    onCreateUserClose();
  };

  return (
    <div>
      <Flex vertical gap={16}>
        <Typography.Paragraph className="mt-2">
          Configure manual tasks for this integration. Manual tasks allow you to
          define custom data collection or processing steps that require human
          intervention.
        </Typography.Paragraph>

        <Flex align="center" justify="space-between" gap={8}>
          <Button type="default" onClick={onCreateUserOpen}>
            Manage secure access
          </Button>
          <Button type="primary" onClick={handleAddManualTask}>
            Add manual task
          </Button>
        </Flex>

        <ManualTaskConfigTable
          integration={integration}
          shouldOpenAddModal={shouldOpenAddModal}
          onAddModalOpenComplete={handleAddModalOpenComplete}
        />
        <Divider className="my-2" />
        <ManualTaskAssignmentSection
          selectedUsers={selectedUsers}
          userOptions={userOptions}
          onUserAssignmentChange={handleUserAssignmentChange}
        />

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
