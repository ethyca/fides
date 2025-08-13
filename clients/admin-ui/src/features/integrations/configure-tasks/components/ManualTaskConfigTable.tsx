import {
  AntTable as Table,
  AntTypography as Typography,
  WarningIcon,
} from "fidesui";
import { useCallback, useEffect, useState } from "react";

import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import { ConnectionConfigurationResponse } from "~/types/api";

import AddManualTaskModal from "../AddManualTaskModal";
import { useManualTaskManagement } from "../hooks/useManualTaskManagement";
import { Task } from "../types";
import { useManualTaskColumns } from "../useManualTaskColumns";

interface ManualTaskConfigTableProps {
  integration: ConnectionConfigurationResponse;
  shouldOpenAddModal?: boolean;
  onAddModalOpenComplete?: () => void;
}

const ManualTaskConfigTable = ({
  integration,
  shouldOpenAddModal,
  onAddModalOpenComplete,
}: ManualTaskConfigTableProps) => {
  const { manualTasks, deleteManualTask, refreshManualTasks } =
    useManualTaskManagement({ integration });

  // Local state for task modals only
  const [editingManualTask, setEditingManualTask] = useState<Task | null>(null);
  const [manualTaskToDelete, setManualTaskToDelete] = useState<Task | null>(
    null,
  );
  const [isAddEditModalOpen, setIsAddEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  // Handle external request to open add modal
  useEffect(() => {
    if (shouldOpenAddModal) {
      setEditingManualTask(null);
      setIsAddEditModalOpen(true);
      onAddModalOpenComplete?.();
    }
  }, [shouldOpenAddModal, onAddModalOpenComplete]);

  const handleEditManualTask = useCallback((task: Task) => {
    setEditingManualTask(task);
    setIsAddEditModalOpen(true);
  }, []);

  const handleDeleteManualTask = useCallback((task: Task) => {
    setManualTaskToDelete(task);
    setIsDeleteModalOpen(true);
  }, []);

  const handleCloseAddEditModal = useCallback(() => {
    setEditingManualTask(null);
    setIsAddEditModalOpen(false);
  }, []);

  const handleCloseDeleteModal = useCallback(() => {
    setManualTaskToDelete(null);
    setIsDeleteModalOpen(false);
  }, []);

  const handleConfirmDelete = useCallback(async () => {
    if (manualTaskToDelete) {
      await deleteManualTask(manualTaskToDelete);
    }
    handleCloseDeleteModal();
  }, [manualTaskToDelete, deleteManualTask, handleCloseDeleteModal]);

  const { columns } = useManualTaskColumns({
    onEdit: handleEditManualTask,
    onDelete: handleDeleteManualTask,
  });

  return (
    <>
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
        onClose={handleCloseAddEditModal}
        integration={integration}
        onTaskAdded={refreshManualTasks}
        editingTask={editingManualTask}
      />

      <ConfirmationModal
        isOpen={isDeleteModalOpen}
        onClose={handleCloseDeleteModal}
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
