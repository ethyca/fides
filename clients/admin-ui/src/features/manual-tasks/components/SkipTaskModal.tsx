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

import { useSkipTaskMutation } from "../manual-tasks.slice";
import { ManualTask } from "../mocked/types";
import { TaskDetails } from "./TaskDetails";

interface SkipTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  task: ManualTask;
}

export const SkipTaskModal = ({
  isOpen,
  onClose,
  task,
}: SkipTaskModalProps) => {
  const [skipTask, { isLoading }] = useSkipTaskMutation();
  const [comment, setComment] = useState("");

  const handleSave = async () => {
    try {
      await skipTask({
        task_id: task.task_id,
        comment,
      }).unwrap();

      // Reset form
      setComment("");
      onClose();
    } catch (error) {
      console.error("Failed to skip task:", error);
    }
  };

  const handleCancel = () => {
    // Reset form
    setComment("");
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
