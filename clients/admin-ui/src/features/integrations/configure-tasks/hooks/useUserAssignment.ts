import { AntMessage as message, useDisclosure } from "fidesui";
import { useCallback, useEffect, useState } from "react";

import {
  useAssignUsersToManualTaskMutation,
  useGetManualTaskConfigQuery,
} from "~/features/datastore-connections/connection-manual-tasks.slice";
import { useGetAllUsersQuery } from "~/features/user-management/user-management.slice";
import { ConnectionConfigurationResponse } from "~/types/api";

interface UseUserAssignmentProps {
  integration: ConnectionConfigurationResponse;
}

export const useUserAssignment = ({ integration }: UseUserAssignmentProps) => {
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [isSavingUsers, setIsSavingUsers] = useState(false);

  // User creation modal state
  const {
    isOpen: isCreateUserOpen,
    onOpen: onCreateUserOpen,
    onClose: onCreateUserClose,
  } = useDisclosure();

  // Get manual task config to load currently assigned users
  const { data: manualTaskConfig } = useGetManualTaskConfigQuery(
    { connectionKey: integration ? integration.key : "" },
    {
      skip: !integration,
    },
  );

  // Get users for the assigned to field
  const { data: usersData, refetch: refetchUsers } = useGetAllUsersQuery({
    page: 1,
    size: 100, // Get enough users for the dropdown
    username: "", // Empty string to get all users
  });

  const [assignUsersToManualTask] = useAssignUsersToManualTaskMutation();

  const users = usersData?.items ?? [];

  // Create options for the assigned to select
  const userOptions = users.map((user: any) => {
    const displayName =
      user.first_name && user.last_name
        ? `${user.first_name} ${user.last_name}`
        : user.email_address;

    return {
      label: `${user.first_name} ${user.last_name} (${user.email_address})`,
      value: user.email_address,
      displayName, // This will be used for the tag display
    };
  });

  // Load currently assigned users when manual task config loads
  useEffect(() => {
    if (manualTaskConfig?.assigned_users) {
      const assignedUserEmails = manualTaskConfig.assigned_users
        .map((user) => user.email_address)
        .filter((email) => email !== null && email !== undefined) as string[];
      setSelectedUsers(assignedUserEmails);
    }
  }, [manualTaskConfig]);

  const handleSaveUserAssignments = useCallback(
    async (userIds?: string[]) => {
      const usersToSave = userIds ?? selectedUsers;
      setIsSavingUsers(true);
      try {
        await assignUsersToManualTask({
          connectionKey: integration.key,
          userIds: usersToSave,
        }).unwrap();
        message.success("Assigned users have been updated");
      } catch (error) {
        message.error(
          "Failed to assign users to manual task. Please try again.",
        );
      } finally {
        setIsSavingUsers(false);
      }
    },
    [assignUsersToManualTask, integration.key, selectedUsers],
  );

  const handleUserAssignmentChange = useCallback(
    (userIds: string[]) => {
      setSelectedUsers(userIds);
      handleSaveUserAssignments(userIds);
    },
    [handleSaveUserAssignments],
  );

  const handleUserCreated = useCallback(() => {
    refetchUsers();
  }, [refetchUsers]);

  return {
    selectedUsers,
    userOptions,
    isSavingUsers,
    handleUserAssignmentChange,
    handleUserCreated,
    // User creation modal
    isCreateUserOpen,
    onCreateUserOpen,
    onCreateUserClose,
  };
};
