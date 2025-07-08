/**
 * COPIED & ADAPTED FROM: clients/admin-ui/src/features/manual-tasks/components/CompleteTaskModal.tsx
 *
 * Key differences for external users:
 * - Uses external Redux hooks and slice
 * - Uses external data-testids for Cypress testing
 * - Simplified error handling for external interface
 * - No admin-specific features or routing
 *
 * IMPORTANT: When updating admin-ui CompleteTaskModal.tsx, review this component for sync!
 */

import {
  AntButton as Button,
  AntCheckbox as Checkbox,
  AntDivider as Divider,
  AntInput as Input,
  AntSpace as Space,
  AntTypography as Typography,
  AntUpload as Upload,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
} from "fidesui";
import { useState } from "react";

import {
  ManualFieldListItem,
  ManualTaskFieldType,
  useCompleteExternalTaskMutation,
} from "../external-manual-tasks.slice";
import { ExternalTaskDetails } from "./ExternalTaskDetails";

interface ExternalCompleteTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  task: ManualFieldListItem;
}

export const ExternalCompleteTaskModal = ({
  isOpen,
  onClose,
  task,
}: ExternalCompleteTaskModalProps) => {
  const [completeTask, { isLoading }] = useCompleteExternalTaskMutation();
  const [textValue, setTextValue] = useState("");
  const [checkboxValue, setCheckboxValue] = useState(false);
  const [comment, setComment] = useState("");
  const [fileList, setFileList] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    try {
      setError(null);

      const getFieldValue = () => {
        if (task.input_type === ManualTaskFieldType.TEXT) {
          return textValue;
        }
        if (task.input_type === ManualTaskFieldType.CHECKBOX) {
          return checkboxValue.toString();
        }
        return undefined;
      };

      await completeTask({
        privacy_request_id: task.privacy_request.id,
        manual_field_id: task.manual_field_id,
        field_key: task.manual_field_id,
        field_value: getFieldValue(),
        comment_text: comment || undefined,
        attachment: fileList.length > 0 ? fileList[0].originFileObj : undefined,
      }).unwrap();

      // Reset form
      setTextValue("");
      setCheckboxValue(false);
      setComment("");
      setFileList([]);
      onClose();
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error("Failed to complete task:", err);
      setError("Failed to complete task. Please try again.");
    }
  };

  const handleCancel = () => {
    // Reset form and error
    setTextValue("");
    setCheckboxValue(false);
    setComment("");
    setFileList([]);
    setError(null);
    onClose();
  };

  // Check if the required field is filled based on input type
  const isRequiredFieldFilled = () => {
    switch (task.input_type) {
      case ManualTaskFieldType.TEXT:
        return textValue.trim().length > 0;
      case ManualTaskFieldType.CHECKBOX:
        return checkboxValue;
      default:
        // For file uploads, require at least one file
        return fileList.length > 0;
    }
  };

  const renderTaskInput = () => {
    switch (task.input_type) {
      case ManualTaskFieldType.TEXT:
        return (
          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-700">
              Subject data
            </div>
            <Input.TextArea
              value={textValue}
              onChange={(e) => setTextValue(e.target.value)}
              placeholder="Enter your response..."
              rows={4}
              data-testid="complete-modal-text-input"
            />
          </div>
        );
      case ManualTaskFieldType.CHECKBOX:
        return (
          <div className="space-y-2">
            <Checkbox
              checked={checkboxValue}
              onChange={(e) => setCheckboxValue(e.target.checked)}
              data-testid="complete-modal-checkbox"
            >
              The task has been completed
            </Checkbox>
          </div>
        );
      default:
        // For file uploads or when input_type is attachment, show file upload
        return (
          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-700">Upload File</div>
            <div>
              <Upload
                fileList={fileList}
                onChange={({ fileList: newFileList }) =>
                  setFileList(newFileList)
                }
                beforeUpload={() => false} // Prevent auto upload
                data-testid="complete-modal-file-upload"
              >
                <Button data-testid="complete-modal-upload-button">
                  Click to Upload
                </Button>
              </Upload>
            </div>
          </div>
        );
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="700px" isCentered>
      <ModalOverlay />
      <ModalContent maxWidth="700px" data-testid="complete-task-modal">
        <ModalHeader>
          <Typography.Title level={4}>Complete Task</Typography.Title>
        </ModalHeader>
        <ModalBody>
          <div className="flex flex-col space-y-6">
            <div>
              <ExternalTaskDetails task={task} />
            </div>

            <Divider />

            <div>
              <div className="flex flex-col space-y-4">
                {renderTaskInput()}

                <div className="space-y-2">
                  <div className="text-sm font-medium text-gray-700">
                    Internal comment
                  </div>
                  <Input.TextArea
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder="Add any additional comments..."
                    rows={3}
                    data-testid="complete-modal-comment-input"
                  />
                </div>
              </div>
            </div>

            {/* Error Display */}
            {error && (
              <div
                className="text-red-600 text-sm"
                data-testid="task-completion-error"
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
              data-testid="complete-modal-cancel-button"
            >
              Cancel
            </Button>
            <Button
              type="primary"
              onClick={handleSave}
              loading={isLoading}
              disabled={!isRequiredFieldFilled()}
              data-testid="complete-modal-save-button"
            >
              Save
            </Button>
          </Space>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
