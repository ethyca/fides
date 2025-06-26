/**
 * COPIED & ADAPTED FROM: clients/admin-ui/src/features/manual-tasks/components/SkipTaskModal.tsx
 *
 * Key differences for external users:
 * - Uses external Redux hooks and slice
 * - Uses external data-testids for Cypress testing
 * - Simplified error handling for external interface
 * - No admin-specific features or routing
 *
 * IMPORTANT: When updating admin-ui SkipTaskModal.tsx, review this component for sync!
 */

import {
  AntButton as Button,
  AntDivider as Divider,
  AntInput as Input,
  AntSpace as Space,
  AntTypography as Typography,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
} from "fidesui";
import { useState } from "react";

import { useSkipExternalTaskMutation } from "../external-manual-tasks.slice";
import { ManualTask } from "../types";
import { ExternalTaskDetails } from "./ExternalTaskDetails";

interface ExternalSkipTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  task: ManualTask;
}

export const ExternalSkipTaskModal = ({
  isOpen,
  onClose,
  task,
}: ExternalSkipTaskModalProps) => {
  const [skipTask, { isLoading }] = useSkipExternalTaskMutation();
  const [comment, setComment] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    try {
      setError(null);
      await skipTask({
        task_id: task.task_id,
        comment,
      }).unwrap();

      // Reset form
      setComment("");
      onClose();
    } catch (err) {
      console.error("Failed to skip task:", err);
      setError("Failed to skip task. Please try again.");
    }
  };

  const handleCancel = () => {
    // Reset form and error
    setComment("");
    setError(null);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="700px" isCentered>
      <ModalOverlay />
      <ModalContent maxWidth="700px" data-testid="skip-task-modal">
        <ModalHeader>
          <Typography.Title level={4}>Skip Task</Typography.Title>
        </ModalHeader>
        <ModalBody>
          <div className="flex flex-col space-y-6">
            {/* Details */}
            <div>
              <ExternalTaskDetails task={task} />
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

            {/* Error Display */}
            {error && (
              <div
                className="text-red-600 text-sm"
                data-testid="skip-task-error"
              >
                {error}
              </div>
            )}
          </div>
        </ModalBody>

        <ModalFooter>
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
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
