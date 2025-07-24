import { getCoreRowModel, useReactTable } from "@tanstack/react-table";
import {
  AntButton as Button,
  AntDivider as Divider,
  AntMessage as message,
  AntSelect as Select,
  AntTypography as Typography,
  Box,
  Flex,
  Text,
  useDisclosure,
  WarningIcon,
} from "fidesui";
import { useCallback, useEffect, useState } from "react";

import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import { FidesTableV2 } from "~/features/common/table/v2";
import {
  useDeleteManualFieldMutation,
  useGetManualFieldsQuery,
} from "~/features/datastore-connections/connection-manual-fields.slice";
import {
  useAssignUsersToManualTaskMutation,
  useGetManualTaskConfigQuery,
} from "~/features/datastore-connections/connection-manual-tasks.slice";
import { useGetAllUsersQuery } from "~/features/user-management/user-management.slice";
import {
  ConnectionConfigurationResponse,
  ManualFieldResponse,
} from "~/types/api";

import AddManualTaskModal from "./AddManualTaskModal";
import CreateExternalUserModal from "./CreateExternalUserModal";
import { Task, useTaskColumns } from "./useTaskColumns";

const { Paragraph } = Typography;

interface TaskConfigTabProps {
  integration: ConnectionConfigurationResponse;
}

const TaskConfigTab = ({ integration }: TaskConfigTabProps) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [isSavingUsers, setIsSavingUsers] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [taskToDelete, setTaskToDelete] = useState<Task | null>(null);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const {
    isOpen: isCreateUserOpen,
    onOpen: onCreateUserOpen,
    onClose: onCreateUserClose,
  } = useDisclosure();
  const {
    isOpen: isDeleteOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();

  const { data, refetch } = useGetManualFieldsQuery(
    { connectionKey: integration ? integration.key : "" },
    {
      skip: !integration,
    },
  );

  // Get manual task config to load currently assigned users
  const { data: manualTaskConfig } = useGetManualTaskConfigQuery(
    { connectionKey: integration ? integration.key : "" },
    {
      skip: !integration,
    },
  );

  const [deleteManualField] = useDeleteManualFieldMutation();
  const [assignUsersToManualTask] = useAssignUsersToManualTaskMutation();

  // Get users for the assigned to field
  const { data: usersData, refetch: refetchUsers } = useGetAllUsersQuery({
    page: 1,
    size: 100, // Get enough users for the dropdown
    username: "", // Empty string to get all users
  });

  const users = usersData?.items ?? [];

  // Create options for the assigned to select (without create new user option)
  const userOptions = users.map((user: any) => ({
    label: `${user.first_name} ${user.last_name} (${user.email_address})`,
    value: user.email_address,
  }));

  useEffect(() => {
    if (data) {
      // Transform the manual fields into task format for the table
      const transformedTasks = data.map((field: ManualFieldResponse) => ({
        id: field.id,
        name: field.label,
        description: field.help_text,
        fieldType: field.field_type,
        requestType: field.request_type,
        originalField: field, // Store original field for editing
      }));
      setTasks(transformedTasks);
    }
  }, [data]);

  // Load currently assigned users when manual task config loads
  useEffect(() => {
    if (manualTaskConfig?.assigned_users) {
      const assignedUserEmails = manualTaskConfig.assigned_users
        .map((user) => user.email_address)
        .filter((email) => email !== null && email !== undefined) as string[];
      setSelectedUsers(assignedUserEmails);
    }
  }, [manualTaskConfig]);

  const deleteTask = useCallback(
    async (task: Task) => {
      try {
        await deleteManualField({
          connectionKey: integration.key as string,
          manualFieldId: task.id,
        }).unwrap();

        refetch();
      } catch (error) {
        message.error("Failed to delete task. Please try again.");
      }
    },
    [deleteManualField, integration.key, refetch],
  );

  const handleEdit = useCallback(
    (task: Task) => {
      setEditingTask(task);
      onOpen();
    },
    [onOpen],
  );

  const handleDelete = useCallback(
    (task: Task) => {
      setTaskToDelete(task);
      onDeleteOpen();
    },
    [onDeleteOpen],
  );

  const handleConfirmDelete = useCallback(async () => {
    if (taskToDelete) {
      await deleteTask(taskToDelete);
      setTaskToDelete(null);
    }
    onDeleteClose();
  }, [taskToDelete, deleteTask, onDeleteClose]);

  const handleAddTask = useCallback(() => {
    setEditingTask(null);
    onOpen();
  }, [onOpen]);

  const handleModalClose = useCallback(() => {
    setEditingTask(null);
    onClose();
  }, [onClose]);

  const handleUserCreated = () => {
    // Refetch users to update the dropdown
    refetchUsers();
    onCreateUserClose();
  };

  const handleUserAssignmentChange = useCallback((userIds: string[]) => {
    setSelectedUsers(userIds);
  }, []);

  const handleSaveUserAssignments = useCallback(async () => {
    setIsSavingUsers(true);
    try {
      await assignUsersToManualTask({
        connectionKey: integration.key,
        userIds: selectedUsers,
      }).unwrap();
      message.success("User assignments saved successfully!");
    } catch (error) {
      message.error("Failed to assign users to task. Please try again.");
    } finally {
      setIsSavingUsers(false);
    }
  }, [assignUsersToManualTask, integration.key, selectedUsers]);

  // Use the custom hook for columns
  const { columns } = useTaskColumns({
    onEdit: handleEdit,
    onDelete: handleDelete,
  });

  const tableInstance = useReactTable<Task>({
    data: tasks,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <Box>
      <Flex direction="column" gap={4}>
        <Typography.Paragraph className="mt-2">
          Configure manual tasks for this integration. Manual tasks allow you to
          define custom data collection or processing steps that require human
          intervention.
        </Typography.Paragraph>

        <Flex justify="flex-end">
          <Flex justify="flex-start" align="center" gap={2}>
            <Button type="primary" onClick={handleAddTask}>
              Add manual task
            </Button>
          </Flex>
        </Flex>

        <FidesTableV2
          tableInstance={tableInstance}
          onRowClick={() => {}}
          emptyTableNotice={
            <Box textAlign="center" p={8}>
              <Paragraph type="secondary">
                No manual tasks configured yet. Click &apos;Add manual
                task&apos; to get started.
              </Paragraph>
            </Box>
          }
        />
        <Divider className="my-2" />
        <Box>
          <Typography.Text strong>Assign tasks to users:</Typography.Text>

          <div className="mt-4 flex items-center gap-2">
            <div className="w-1/2">
              <Select
                className="!mt-0"
                placeholder="Select users to assign tasks to"
                mode="multiple"
                maxTagCount="responsive"
                value={selectedUsers}
                onChange={handleUserAssignmentChange}
                options={userOptions}
                style={{ width: "100%", marginTop: 8 }}
                tokenSeparators={[","]}
                filterOption={(input, option) => {
                  return (
                    (typeof option?.label === "string" &&
                      option.label
                        .toLowerCase()
                        .includes(input.toLowerCase())) ||
                    false
                  );
                }}
              />
            </div>

            <Button
              type="primary"
              onClick={handleSaveUserAssignments}
              loading={isSavingUsers}
            >
              Save
            </Button>
          </div>
          <div className="mt-4">
            <Typography.Text strong>Secure access:</Typography.Text>
            <div className="mt-2">
              <Button type="default" onClick={onCreateUserOpen}>
                Manage secure access
              </Button>
            </div>
          </div>
        </Box>

        <AddManualTaskModal
          isOpen={isOpen}
          onClose={handleModalClose}
          integration={integration}
          onTaskAdded={() => {
            refetch();
          }}
          editingTask={editingTask}
        />

        <CreateExternalUserModal
          isOpen={isCreateUserOpen}
          onClose={onCreateUserClose}
          onUserCreated={handleUserCreated}
        />

        <ConfirmationModal
          isOpen={isDeleteOpen}
          onClose={() => {
            setTaskToDelete(null);
            onDeleteClose();
          }}
          onConfirm={handleConfirmDelete}
          title="Delete manual task"
          message={
            <Text color="gray.500">
              Are you sure you want to delete the task &ldquo;
              {taskToDelete?.name}&rdquo;? This action cannot be undone.
            </Text>
          }
          continueButtonText="Delete"
          isCentered
          icon={<WarningIcon />}
        />
      </Flex>
    </Box>
  );
};

export default TaskConfigTab;
