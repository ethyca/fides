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
  useDisclosure,
} from "fidesui";
import { useState } from "react";

import { useCompleteTaskMutation } from "../manual-tasks.slice";
import { ManualTask } from "../mocked/types";
import { SkipTaskModal } from "./SkipTaskModal";
import { TaskDetails } from "./TaskDetails";

interface CompleteTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  task: ManualTask;
}

export const CompleteTaskModal = ({
  isOpen,
  onClose,
  task,
}: CompleteTaskModalProps) => {
  const [completeTask, { isLoading }] = useCompleteTaskMutation();
  const [textValue, setTextValue] = useState("");
  const [checkboxValue, setCheckboxValue] = useState(false);
  const [comment, setComment] = useState("");
  const [fileList, setFileList] = useState<any[]>([]);
  const {
    isOpen: isSkipModalOpen,
    onOpen: onSkipModalOpen,
    onClose: onSkipModalClose,
  } = useDisclosure();

  const handleSave = async () => {
    try {
      await completeTask({
        task_id: task.task_id,
        text_value: task.input_type === "string" ? textValue : undefined,
        checkbox_value:
          task.input_type === "checkbox" ? checkboxValue : undefined,
        attachment_type: fileList.length > 0 ? "file" : undefined,
        comment: comment || undefined,
      }).unwrap();

      // Reset form
      setTextValue("");
      setCheckboxValue(false);
      setComment("");
      setFileList([]);
      onClose();
    } catch (error) {
      console.error("Failed to complete task:", error);
    }
  };

  const handleCancel = () => {
    // Reset form
    setTextValue("");
    setCheckboxValue(false);
    setComment("");
    setFileList([]);
    onClose();
  };

  const handleSkipTask = () => {
    onClose();
    onSkipModalOpen();
  };

  // Check if the required field is filled based on input type
  const isRequiredFieldFilled = () => {
    switch (task.input_type) {
      case "string":
        return textValue.trim().length > 0;
      case "checkbox":
        return checkboxValue;
      default:
        // For file uploads, require at least one file
        return fileList.length > 0;
    }
  };

  const renderTaskInput = () => {
    switch (task.input_type) {
      case "string":
        return (
          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-700">Text Input</div>
            <Input.TextArea
              value={textValue}
              onChange={(e) => setTextValue(e.target.value)}
              placeholder="Enter your response..."
              rows={4}
            />
          </div>
        );
      case "checkbox":
        return (
          <div className="space-y-2">
            <Checkbox
              checked={checkboxValue}
              onChange={(e) => setCheckboxValue(e.target.checked)}
            >
              The task has been completed
            </Checkbox>
          </div>
        );
      default:
        // For file uploads or when input_type is undefined, show file upload
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
              >
                <Button>Click to Upload</Button>
              </Upload>
            </div>
          </div>
        );
    }
  };

  return (
    <>
      <Modal isOpen={isOpen} onClose={onClose} size="700px" isCentered>
        <ModalOverlay />
        <ModalContent maxWidth="700px">
          <ModalHeader>
            <Typography.Title level={4}>Complete Task</Typography.Title>
          </ModalHeader>
          <ModalBody>
            <div className="flex flex-col space-y-6">
              <div>
                <TaskDetails task={task} />
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
                    />
                  </div>
                </div>
              </div>
            </div>
          </ModalBody>

          <ModalFooter>
            <div className="flex w-full justify-between">
              <Button onClick={handleSkipTask} disabled={isLoading}>
                Skip task
              </Button>
              <Space>
                <Button onClick={handleCancel} disabled={isLoading}>
                  Cancel
                </Button>
                <Button
                  type="primary"
                  onClick={handleSave}
                  loading={isLoading}
                  disabled={!isRequiredFieldFilled()}
                >
                  Save
                </Button>
              </Space>
            </div>
          </ModalFooter>
        </ModalContent>
      </Modal>

      <SkipTaskModal
        isOpen={isSkipModalOpen}
        onClose={onSkipModalClose}
        task={task}
      />
    </>
  );
};
