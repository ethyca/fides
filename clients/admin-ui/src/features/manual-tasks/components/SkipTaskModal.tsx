import { Button, Divider, Input, Modal, Space, useMessage } from "fidesui";
import { useState } from "react";

import { MODAL_SIZE } from "~/features/common/modals/modal-sizes";
import { ManualFieldListItem } from "~/types/api";

import { useSkipTaskMutation } from "../manual-tasks.slice";
import { TaskDetails } from "./TaskDetails";

interface SkipTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  task: ManualFieldListItem;
}

export const SkipTaskModal = ({
  isOpen,
  onClose,
  task,
}: SkipTaskModalProps) => {
  const [skipTask, { isLoading }] = useSkipTaskMutation();
  const [comment, setComment] = useState("");

  const message = useMessage();

  const handleSave = async () => {
    try {
      await skipTask({
        privacy_request_id: task.privacy_request.id,
        manual_field_id: task.manual_field_id,
        skip_reason: comment,
      }).unwrap();

      // Reset form
      setComment("");
      onClose();
    } catch (error) {
      message.error("Failed to skip task. Please try again.");
    }
  };

  const handleCancel = () => {
    // Reset form
    setComment("");
    onClose();
  };

  return (
    <Modal
      open={isOpen}
      onCancel={onClose}
      centered
      destroyOnClose
      width={MODAL_SIZE.lg}
      data-testid="skip-task-modal"
      title="Skip Task"
      footer={
        <Space>
          <Button
            onClick={handleCancel}
            disabled={isLoading}
            data-testid="skip-modal-cancel-button"
          >
            Cancel
          </Button>
          <Button
            type="primary"
            onClick={handleSave}
            loading={isLoading}
            disabled={!comment.trim()}
            danger
            data-testid="skip-modal-skip-button"
          >
            Skip Task
          </Button>
        </Space>
      }
    >
      <div className="flex flex-col space-y-6">
        {/* Details */}
        <div>
          <TaskDetails task={task} />
        </div>

        {/* Divider for separation */}
        <Divider />

        {/* Skip Reason Section */}
        <div>
          <div className="flex flex-col space-y-4">
            <div className="space-y-2">
              <div className="text-sm font-medium text-gray-700">
                Reason for skipping (Required)
              </div>
              <Input.TextArea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Please provide a reason for skipping this task..."
                rows={4}
                data-testid="skip-modal-comment-input"
              />
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
};
