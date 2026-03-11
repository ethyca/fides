import { Button, Flex, List, Typography, useModal, WarningIcon } from "fidesui";
import { useState } from "react";

import { ConnectionConfigurationResponse } from "~/types/api";

import AddManualTaskModal from "../AddManualTaskModal";
import { REQUEST_TYPE_LABELS } from "../constants";
import { useManualTaskManagement } from "../hooks/useManualTaskManagement";
import { Task } from "../types";

interface ManualTaskConfigListProps {
  integration: ConnectionConfigurationResponse;
}

const ManualTaskConfigList = ({ integration }: ManualTaskConfigListProps) => {
  const { manualTasks, deleteManualTask, refreshManualTasks } =
    useManualTaskManagement({ integration });

  // Local state for task modals only
  const [editingManualTask, setEditingManualTask] = useState<Task | null>(null);
  const [isAddEditModalOpen, setIsAddEditModalOpen] = useState(false);
  const modal = useModal();

  const handleAddManualTask = () => {
    setEditingManualTask(null);
    setIsAddEditModalOpen(true);
  };

  const handleEdit = (task: Task) => {
    setEditingManualTask(task);
    setIsAddEditModalOpen(true);
  };

  const handleDelete = (task: Task) => {
    modal.confirm({
      title: "Delete manual task",
      content: (
        <span className="text-gray-500">
          Are you sure you want to delete the manual task &quot;
          {task.name}&quot;? This action cannot be undone.
        </span>
      ),
      okText: "Delete",
      centered: true,
      icon: <WarningIcon />,
      onOk: () => deleteManualTask(task),
    });
  };

  return (
    <>
      <Flex align="center" justify="end" gap="small" className="mt-[-25px]">
        <Button
          type="primary"
          onClick={handleAddManualTask}
          data-testid="add-manual-task-list-btn"
        >
          Create manual task
        </Button>
      </Flex>

      <List
        itemLayout="horizontal"
        dataSource={manualTasks}
        locale={{
          emptyText: (
            <div className="px-4 py-2 text-center">
              <Typography.Paragraph type="secondary">
                No manual tasks configured yet. <br />
                Click &quot;Create manual task&quot; to get started.
              </Typography.Paragraph>
            </div>
          ),
        }}
        renderItem={(task: Task) => {
          const requestTypeLabel =
            REQUEST_TYPE_LABELS[
              task.requestType as keyof typeof REQUEST_TYPE_LABELS
            ] || task.requestType;

          return (
            <List.Item
              key={task.id}
              actions={[
                <Button
                  key="edit"
                  type="link"
                  onClick={() => handleEdit(task)}
                  data-testid="edit-list-btn"
                  className="px-1"
                >
                  Edit
                </Button>,
                <Button
                  key="delete"
                  type="link"
                  onClick={() => handleDelete(task)}
                  data-testid="delete-list-btn"
                  className="px-1"
                >
                  Delete
                </Button>,
              ]}
            >
              <List.Item.Meta
                title={`${task.name} (${requestTypeLabel})`}
                description={task.description}
              />
            </List.Item>
          );
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
    </>
  );
};

export default ManualTaskConfigList;
