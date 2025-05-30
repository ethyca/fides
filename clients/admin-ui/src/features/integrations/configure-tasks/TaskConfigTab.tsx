import {
  ColumnDef,
  createColumnHelper,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  AntButton as Button,
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
  useGetAccessManualHookQuery,
  usePatchAccessManualWebhookMutation,
} from "~/features/datastore-connections/datastore-connection.slice";
import { ConnectionConfigurationResponse } from "~/types/api";

import AddManualTaskModal from "./AddManualTaskModal";
import { TASK_INPUT_TYPE_LABELS, TaskInputType } from "./types";

const { Title, Paragraph } = Typography;

interface TaskConfigTabProps {
  integration: ConnectionConfigurationResponse;
}

interface Task {
  id: string;
  name: string;
  description: string;
  types: string;
  originalField: any; // Store the original field data for editing
}

const columnHelper = createColumnHelper<Task>();

const TaskConfigTab = ({ integration }: TaskConfigTabProps) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const { isOpen, onOpen, onClose } = useDisclosure();

  const { data, refetch } = useGetAccessManualHookQuery(
    integration ? integration.key : "",
    {
      skip: !integration,
    },
  );

  const [patchAccessManualWebhook] = usePatchAccessManualWebhookMutation();

  useEffect(() => {
    if (data && data.fields) {
      // Transform the data.fields into task format for the table
      const transformedTasks = data.fields.map((field: any, index: number) => ({
        id: `${index}`,
        name: field.pii_field || `Task ${index + 1}`,
        description: field.dsr_package_label || "Manual task",
        types: field.types
          ? field.types
              .map(
                (type: TaskInputType) => TASK_INPUT_TYPE_LABELS[type] || type,
              )
              .join(", ")
          : "N/A",
        originalField: field, // Store original field for editing
      }));
      setTasks(transformedTasks);
    }
  }, [data]);

  const deleteTask = async (task: Task) => {
    try {
      // Remove the task from the fields array
      const updatedFields =
        data?.fields?.filter((_, index) => index.toString() !== task.id) || [];

      await patchAccessManualWebhook({
        connection_key: integration.key as string,
        body: { fields: updatedFields },
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
  const renderTypes = (props: any) => <DefaultCell value={props.getValue()} />;

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
  const renderTypesHeader = (props: any) => (
    <DefaultHeaderCell value="Types" {...props} />
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
      columnHelper.accessor((row) => row.types, {
        id: "types",
        cell: renderTypes,
        header: renderTypesHeader,
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
    <Box maxW="760px">
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
        />
      </Flex>
    </Box>
  );
};

export default TaskConfigTab;
