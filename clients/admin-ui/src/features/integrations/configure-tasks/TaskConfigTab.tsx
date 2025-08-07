import { getCoreRowModel, useReactTable } from "@tanstack/react-table";
import {
  AntButton as Button,
  AntDivider as Divider,
  AntMessage as message,
  AntTypography as Typography,
  Box,
  Flex,
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
// import { useGetManualTaskConfigQuery } from "~/features/datastore-connections/connection-manual-tasks.slice";
import {
  ConnectionConfigurationResponse,
  ManualFieldResponse,
} from "~/types/api";

import AddManualTaskModal from "./AddManualTaskModal";
import CreateExternalUserModal from "./CreateExternalUserModal";
import TaskAssignedUsersSection from "./TaskAssignedUsersSection";
import TaskCreationConditions from "./TaskCreationConditions";
import { Task, useTaskColumns } from "./useTaskColumns";

const { Paragraph } = Typography;

interface TaskConfigTabProps {
  integration: ConnectionConfigurationResponse;
}

const TaskConfigTab = ({ integration }: TaskConfigTabProps) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  // State handled in TaskAssignedUsersSection
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

  // Manual task config not needed directly here post-refactor

  const [deleteManualField] = useDeleteManualFieldMutation();
  // Users and assignment logic moved to TaskAssignedUsersSection

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

  // Assignment state moved to TaskAssignedUsersSection

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
    onCreateUserClose();
  };

  // Assignment handlers moved to TaskAssignedUsersSection

  // Deprecated multi-assign flow replaced by single-assign UX (handled in child)

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

        <div>
          <TaskAssignedUsersSection
            connectionKey={integration.key}
            onManageSecureAccess={onCreateUserOpen}
          />
        </div>

        {isManualTaskConditionsEnabled && (
          <>
            <Divider className="my-2" />

            <TaskCreationConditions connectionKey={integration.key} />
          </>
        )}

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
