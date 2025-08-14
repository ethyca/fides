import {
  AntButton as Button,
  AntFlex as Flex,
  AntTable as Table,
  AntTypography as Typography,
  WarningIcon,
} from "fidesui";
import { useCallback, useState } from "react";

import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import { ConnectionConfigurationResponse } from "~/types/api";

import AddManualTaskModal from "../AddManualTaskModal";
import { useManualTaskManagement } from "../hooks/useManualTaskManagement";
import { Task } from "../types";
import { useManualTaskColumns } from "../useManualTaskColumns";

interface ManualTaskConfigTableProps {
  integration: ConnectionConfigurationResponse;
}

const ManualTaskConfigTable = ({ integration }: ManualTaskConfigTableProps) => {
  const { manualTasks, deleteManualTask, refreshManualTasks } =
    useManualTaskManagement({ integration });

  // Local state for task modals only
  const [editingManualTask, setEditingManualTask] = useState<Task | null>(null);
  const [manualTaskToDelete, setManualTaskToDelete] = useState<Task | null>(
    null,
  );
  const [isAddEditModalOpen, setIsAddEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  const handleAddManualTask = () => {
    setEditingManualTask(null);
    setIsAddEditModalOpen(true);
  };

  const handleConfirmDelete = useCallback(async () => {
    if (manualTaskToDelete) {
      await deleteManualTask(manualTaskToDelete);
    }
    // Close delete modal
    setManualTaskToDelete(null);
    setIsDeleteModalOpen(false);
  }, [manualTaskToDelete, deleteManualTask]);

  const { columns } = useManualTaskColumns({
    onEdit: (task: Task) => {
      setEditingManualTask(task);
      setIsAddEditModalOpen(true);
    },
    onDelete: (task: Task) => {
      setManualTaskToDelete(task);
      setIsDeleteModalOpen(true);
    },
  });

  return (
    <>
      <Flex align="center" justify="end" gap={8} className="mb-1 mt-[-25px]">
        <Button
          type="primary"
          onClick={handleAddManualTask}
          data-testid="add-manual-task-btn"
        >
          Add manual task
        </Button>
      </Flex>

      <Table
        columns={columns}
        dataSource={manualTasks}
        rowKey="id"
        pagination={false}
        locale={{
          emptyText: (
            <div className="p-8 text-center">
              <Typography.Paragraph type="secondary">
                No manual tasks configured yet. Click &apos;Add manual
                task&apos; to get started.
              </Typography.Paragraph>
            </div>
          ),
        }}
      />

      <AddManualTaskModal
        isOpen={isAddEditModalOpen}
        onClose={() => {
          setEditingManualTask(null);
          setIsAddEditModalOpen(false);
        }}
        integration={integration}
        onTaskAdded={refreshManualTasks}
        editingTask={editingManualTask}
      />

      <ConfirmationModal
        isOpen={isDeleteModalOpen}
        onClose={() => {
          setManualTaskToDelete(null);
          setIsDeleteModalOpen(false);
        }}
        onConfirm={handleConfirmDelete}
        title="Delete manual task"
        message={
          <span className="text-gray-500">
            Are you sure you want to delete the manual task &ldquo;
            {manualTaskToDelete?.name}&rdquo;? This action cannot be undone.
          </span>
        }
        continueButtonText="Delete"
        isCentered
        icon={<WarningIcon />}
      />
    </>
  );
};

export default ManualTaskConfigTable;
