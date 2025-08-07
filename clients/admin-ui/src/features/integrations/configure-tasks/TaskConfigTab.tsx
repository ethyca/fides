import { getCoreRowModel, useReactTable } from "@tanstack/react-table";
import {
  AntButton as Button,
  AntDivider as Divider,
  AntMessage as message,
  AntSelect as Select,
  AntTable as Table,
  AntTypography as Typography,
  Box,
  Flex,
  Icons,
  Text,
  useDisclosure,
  WarningIcon,
} from "fidesui";
import { useCallback, useEffect, useState } from "react";

import { useFlags } from "~/features/common/features";
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
import TaskCreationConditions from "./TaskCreationConditions";
import { Task, useTaskColumns } from "./useTaskColumns";

const { Paragraph } = Typography;

interface TaskConfigTabProps {
  integration: ConnectionConfigurationResponse;
}

const TaskConfigTab = ({ integration }: TaskConfigTabProps) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [userToAssign, setUserToAssign] = useState<string | undefined>(
    undefined,
  );
  const [isSavingUsers, setIsSavingUsers] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [taskToDelete, setTaskToDelete] = useState<Task | null>(null);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { flags } = useFlags();
  const isManualTaskConditionsEnabled = flags.alphaManualTaskConditions;

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

  // Options for assignment: exclude users already assigned
  const availableUserOptions = users
    .filter((user: any) => {
      const email = user.email_address;
      return email && !selectedUsers.includes(email);
    })
    .map((user: any) => ({
      label: `${user.first_name ?? ""} ${user.last_name ?? ""}`.trim()
        ? `${user.first_name ?? ""} ${user.last_name ?? ""} (${user.email_address})`
        : `${user.email_address}`,
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

  const handleAssignSingleUser = useCallback(
    async (email?: string) => {
      if (!email) {
        message.warning("Please select a user to assign.");
        return;
      }
      try {
        setIsSavingUsers(true);
        const updated = Array.from(new Set([...(selectedUsers ?? []), email]));
        await assignUsersToManualTask({
          connectionKey: integration.key,
          userIds: updated,
        }).unwrap();
        setSelectedUsers(updated);
        setUserToAssign(undefined);
        message.success("User assigned successfully!");
      } catch (error) {
        message.error("Failed to assign user. Please try again.");
      } finally {
        setIsSavingUsers(false);
      }
    },
    [assignUsersToManualTask, integration.key, selectedUsers],
  );

  const handleRemoveAssignedUser = useCallback(
    async (email: string) => {
      try {
        setIsSavingUsers(true);
        const updated = (selectedUsers ?? []).filter((e) => e !== email);
        await assignUsersToManualTask({
          connectionKey: integration.key,
          userIds: updated,
        }).unwrap();
        setSelectedUsers(updated);
        message.success("User removed successfully!");
      } catch (error) {
        message.error("Failed to remove user. Please try again.");
      } finally {
        setIsSavingUsers(false);
      }
    },
    [assignUsersToManualTask, integration.key, selectedUsers],
  );

  // Deprecated multi-assign flow replaced by single-assign UX

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

          {/* Top controls */}
          <div className="mt-4 flex items-center justify-between gap-4">
            <div>
              <Button type="default" onClick={onCreateUserOpen}>
                Manage secure access
              </Button>
            </div>
            <div className="flex w-1/2 items-center justify-end gap-2">
              <Select
                className="!mt-0"
                placeholder="Select a user to assign"
                value={userToAssign}
                onChange={(val) => setUserToAssign(val)}
                options={availableUserOptions}
                style={{ width: "100%" }}
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
              <Button
                type="primary"
                onClick={() => handleAssignSingleUser(userToAssign)}
                loading={isSavingUsers}
              >
                Assign
              </Button>
            </div>
          </div>

          {/* Assigned users table */}
          <div className="mt-4">
            <Table
              dataSource={(manualTaskConfig?.assigned_users || []).map(
                (u, idx) => ({
                  key: u.email_address ?? idx,
                  name: `${u.first_name ?? ""} ${u.last_name ?? ""}`.trim(),
                  email: u.email_address ?? "",
                  role: "—",
                  raw: u,
                }),
              )}
              pagination={false}
              size="small"
              columns={[
                {
                  title: "Name",
                  dataIndex: "name",
                  key: "name",
                },
                {
                  title: "Email",
                  dataIndex: "email",
                  key: "email",
                },
                {
                  title: "Role",
                  dataIndex: "role",
                  key: "role",
                  render: () => <span>—</span>,
                },
                {
                  title: "Actions",
                  key: "actions",
                  width: 120,
                  render: (_: any, record: any) => (
                    <Flex gap={2}>
                      <Button
                        size="small"
                        danger
                        icon={<Icons.TrashCan />}
                        onClick={() =>
                          record.email && handleRemoveAssignedUser(record.email)
                        }
                      />
                    </Flex>
                  ),
                },
              ]}
              locale={{
                emptyText: (
                  <div className="py-6 text-center">
                    <Text color="gray.500">No users assigned.</Text>
                  </div>
                ),
              }}
              bordered
            />
          </div>

          {isManualTaskConditionsEnabled && (
            <div className="mt-4">
              <TaskCreationConditions connectionKey={integration.key} />
            </div>
          )}
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
