import { getCoreRowModel, useReactTable } from "@tanstack/react-table";
import type { MenuProps } from "antd";
import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntSelect as Select,
  AntTypography as Typography,
  Box,
  Flex,
  Icons,
  useDisclosure,
} from "fidesui";
import { useCallback, useEffect, useState } from "react";

import { FidesTableV2 } from "~/features/common/table/v2";
import {
  useDeleteManualFieldMutation,
  useGetManualFieldsQuery,
} from "~/features/datastore-connections/connection-manual-fields.slice";
import { useAssignUsersToManualTaskMutation } from "~/features/datastore-connections/connection-manual-tasks.slice";
import { useGetAllUsersQuery } from "~/features/user-management/user-management.slice";
import {
  ConnectionConfigurationResponse,
  ManualFieldResponse,
} from "~/types/api";

import AddManualTaskModal from "./AddManualTaskModal";
import CreateExternalUserModal from "./CreateExternalUserModal";
import { Task, useTaskColumns } from "./useTaskColumns";

const { Title, Paragraph } = Typography;

interface TaskConfigTabProps {
  integration: ConnectionConfigurationResponse;
}

const TaskConfigTab = ({ integration }: TaskConfigTabProps) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const {
    isOpen: isCreateUserOpen,
    onOpen: onCreateUserOpen,
    onClose: onCreateUserClose,
  } = useDisclosure();

  const { data, refetch } = useGetManualFieldsQuery(
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

  const deleteTask = useCallback(
    async (task: Task) => {
      try {
        await deleteManualField({
          connectionKey: integration.key as string,
          manualFieldId: task.id,
        }).unwrap();

        refetch();
      } catch (error) {
        console.error("Error deleting task:", error);
      }
    },
    [deleteManualField, integration.key, refetch],
  );

  const handleEdit = useCallback((task: Task) => {
    // TODO: Implement edit functionality
    console.log("Edit task:", task);
  }, []);

  const handleDelete = useCallback(
    (task: Task) => {
      const confirmed = window.confirm(
        `Are you sure you want to delete the task "${task.name}"?`,
      );

      if (confirmed) {
        deleteTask(task);
      }
    },
    [deleteTask],
  );

  // Menu items for the dropdown
  const menuItems: MenuProps["items"] = [
    {
      key: "manage-access",
      label: "Manage secure access",
      onClick: onCreateUserOpen,
    },
  ];

  const handleUserCreated = () => {
    // Refetch users to update the dropdown
    refetchUsers();
    onCreateUserClose();
  };

  const handleUserAssignmentChange = useCallback(
    async (userIds: string[]) => {
      setSelectedUsers(userIds);

      try {
        await assignUsersToManualTask({
          connectionKey: integration.key,
          userIds,
        }).unwrap();
      } catch (error) {
        console.error("Error assigning users to manual task:", error);
      }
    },
    [assignUsersToManualTask, integration.key],
  );

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
        <div>
          <Paragraph>
            Lorem ipsum dolor sit amet consectetur adipisicing elit. Sit amet
            iusto, nobis dignissimos obcaecati perferendis unde consectetur
            delectus laborum autem fuga reprehenderit quibusdam ipsum,
            laudantium tenetur omnis odit earum molestiae.
            <br />
            Lorem ipsum dolor sit amet consectetur adipisicing elit. Sit amet
            iusto, nobis dignissimos obcaecati perferendis unde consectetur
            delectus laborum autem fuga reprehenderit quibusdam ipsum,
            laudantium tenetur omnis odit earum molestiae.
          </Paragraph>
        </div>

        <Flex justify="flex-end" className="mt-6">
          <Flex justify="flex-start" align="center" gap={2}>
            <Button type="primary" onClick={onOpen}>
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

        <Box className="mt-4">
          <Typography.Text strong>Assign tasks to users:</Typography.Text>
          <div className="w-1/2">
            <Select
              mode="tags"
              placeholder="Select users to assign tasks to"
              value={selectedUsers}
              onChange={handleUserAssignmentChange}
              options={userOptions}
              style={{ width: "100%", marginTop: 8 }}
              tokenSeparators={[","]}
              filterOption={(input, option) => {
                return (
                  (typeof option?.label === "string" &&
                    option.label.toLowerCase().includes(input.toLowerCase())) ||
                  false
                );
              }}
            />
          </div>
          <div className="mt-4 flex ">
            <Button type="default" onClick={onCreateUserOpen}>
              Manage secure access
            </Button>
            <Button type="primary">Save</Button>
          </div>
        </Box>

        <AddManualTaskModal
          isOpen={isOpen}
          onClose={onClose}
          integration={integration}
          onTaskAdded={() => {
            refetch();
          }}
          selectedUsers={selectedUsers}
        />

        <CreateExternalUserModal
          isOpen={isCreateUserOpen}
          onClose={onCreateUserClose}
          onUserCreated={handleUserCreated}
        />
      </Flex>
    </Box>
  );
};

export default TaskConfigTab;
