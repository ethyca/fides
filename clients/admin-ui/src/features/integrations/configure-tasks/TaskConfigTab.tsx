import {
  ColumnDef,
  createColumnHelper,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  AntButton as Button,
  AntSelect as Select,
  AntTypography as Typography,
  Box,
  Flex,
  Icons,
  useDisclosure,
} from "fidesui";
import { useEffect, useMemo, useState } from "react";

import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
} from "~/features/common/table/v2";
import {
  useDeleteManualFieldMutation,
  useGetManualFieldsQuery,
} from "~/features/datastore-connections/connection-manual-fields.slice";
import { useGetAllUsersQuery } from "~/features/user-management/user-management.slice";
import {
  ConnectionConfigurationResponse,
  ManualFieldResponse,
} from "~/types/api";

import AddManualTaskModal from "./AddManualTaskModal";

const { Title, Paragraph } = Typography;

interface TaskConfigTabProps {
  integration: ConnectionConfigurationResponse;
}

interface Task {
  id: string;
  name: string;
  description: string;
  fieldType: string;
  requestType: string;
  originalField: ManualFieldResponse; // Store the original field data for editing
}

const columnHelper = createColumnHelper<Task>();

const TaskConfigTab = ({ integration }: TaskConfigTabProps) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const { isOpen, onOpen, onClose } = useDisclosure();

  const { data, refetch } = useGetManualFieldsQuery(
    { connectionKey: integration ? integration.key : "" },
    {
      skip: !integration,
    },
  );

  const [deleteManualField] = useDeleteManualFieldMutation();

  // Get users for the assigned to field
  const { data: usersData } = useGetAllUsersQuery({
    page: 1,
    size: 100, // Get enough users for the dropdown
    username: "", // Empty string to get all users
  });

  const users = usersData?.items ?? [];

  // Create options for the assigned to select
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

  const deleteTask = async (task: Task) => {
    try {
      await deleteManualField({
        connectionKey: integration.key as string,
        manualFieldId: task.id,
      }).unwrap();

      refetch();
    } catch (error) {
      console.error("Error deleting task:", error);
    }
  };

  const handleEdit = (task: Task) => {
    // TODO: Implement edit functionality
    console.log("Edit task:", task);
  };

  const handleDelete = (task: Task) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete the task "${task.name}"?`,
    );

    if (confirmed) {
      deleteTask(task);
    }
  };

  const renderTaskName = (props: any) => (
    <DefaultCell value={props.getValue()} />
  );
  const renderDescription = (props: any) => (
    <DefaultCell value={props.getValue()} />
  );
  const renderFieldType = (props: any) => (
    <DefaultCell value={props.getValue()} />
  );
  const renderRequestType = (props: any) => (
    <DefaultCell value={props.getValue()} />
  );

  const renderActions = (props: any) => {
    const task = props.row.original;
    return (
      <Flex gap={2}>
        <Button
          size="small"
          icon={<Icons.Edit />}
          onClick={() => handleEdit(task)}
        />
        <Button
          size="small"
          danger
          icon={<Icons.TrashCan />}
          onClick={() => handleDelete(task)}
        />
      </Flex>
    );
  };

  const renderTaskNameHeader = (props: any) => (
    <DefaultHeaderCell value="Task Name" {...props} />
  );
  const renderDescriptionHeader = (props: any) => (
    <DefaultHeaderCell value="Description" {...props} />
  );
  const renderFieldTypeHeader = (props: any) => (
    <DefaultHeaderCell value="Field Type" {...props} />
  );
  const renderRequestTypeHeader = (props: any) => (
    <DefaultHeaderCell value="Request Type" {...props} />
  );
  const renderActionsHeader = (props: any) => (
    <DefaultHeaderCell value="Actions" {...props} />
  );

  const columns: ColumnDef<Task, any>[] = useMemo(
    () => [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: renderTaskName,
        header: renderTaskNameHeader,
      }),
      columnHelper.accessor((row) => row.description, {
        id: "description",
        cell: renderDescription,
        header: renderDescriptionHeader,
      }),
      columnHelper.accessor((row) => row.fieldType, {
        id: "fieldType",
        cell: renderFieldType,
        header: renderFieldTypeHeader,
      }),
      columnHelper.accessor((row) => row.requestType, {
        id: "requestType",
        cell: renderRequestType,
        header: renderRequestTypeHeader,
      }),
      columnHelper.display({
        id: "actions",
        cell: renderActions,
        header: renderActionsHeader,
        meta: { disableRowClick: true },
      }),
    ],
    [],
  );

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
            Configure and manage manual tasks for this integration. Tasks allow
            you to perform specific actions or operations related to your{" "}
            {integration.connection_type} integration.
          </Paragraph>
        </div>

        <Flex justify="space-between" align="center">
          <Title level={5}>Configured Tasks</Title>
          <Button type="primary" onClick={onOpen}>
            Add manual task
          </Button>
        </Flex>

        <Box>
          <Typography.Text strong>Assign tasks to users:</Typography.Text>
          <Select
            mode="tags"
            placeholder="Select users to assign tasks to"
            value={selectedUsers}
            onChange={setSelectedUsers}
            options={userOptions}
            style={{ width: "100%", marginTop: 8 }}
            tokenSeparators={[","]}
            filterOption={(input, option) =>
              option?.label?.toLowerCase().includes(input.toLowerCase()) ||
              false
            }
          />
        </Box>

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

        <AddManualTaskModal
          isOpen={isOpen}
          onClose={onClose}
          integration={integration}
          onTaskAdded={() => {
            refetch();
          }}
          selectedUsers={selectedUsers}
        />
      </Flex>
    </Box>
  );
};

export default TaskConfigTab;
