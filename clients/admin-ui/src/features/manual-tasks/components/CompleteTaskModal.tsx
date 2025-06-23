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

import { useCompleteTaskMutation } from "../manual-tasks.slice";
import { ManualTask } from "../mocked/types";

interface CompleteTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  task: ManualTask;
}

// Helper component for displaying task information rows
const TaskInfoRow = ({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) => (
  <div className="flex items-center">
    <div className="shrink-0 grow-0 basis-1/3 pr-2">
      <Typography.Text className="text-gray-700">{label}:</Typography.Text>
    </div>
    <div className="min-w-0 shrink grow text-gray-600">{children}</div>
  </div>
);

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

  const renderTaskInput = () => {
    switch (task.input_type) {
      case "string":
        return (
          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-700">
              Task Response
            </div>
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
              Mark as completed
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
    <Modal isOpen={isOpen} onClose={onClose} size="700px" isCentered>
      <ModalOverlay />
      <ModalContent maxWidth="700px">
        <ModalHeader>
          <Typography.Title level={4}>Complete Task</Typography.Title>
        </ModalHeader>
        <ModalBody>
          <div className="flex flex-col space-y-6">
            {/* Details */}
            <div>
              <div className="flex flex-col space-y-3">
                <TaskInfoRow label="Name">
                  <Typography.Text>{task.name}</Typography.Text>
                </TaskInfoRow>

                <TaskInfoRow label="Description">
                  <Typography.Text>{task.description}</Typography.Text>
                </TaskInfoRow>

                <TaskInfoRow label="Request Type">
                  <Typography.Text>
                    {task.privacy_request.request_type.charAt(0).toUpperCase() +
                      task.privacy_request.request_type.slice(1)}
                  </Typography.Text>
                </TaskInfoRow>

                <TaskInfoRow label="Assigned To">
                  {task.assigned_users.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                      {task.assigned_users.map((user) => (
                        <span
                          key={user.id}
                          className="inline-flex items-center rounded bg-gray-100 px-2 py-1 text-xs text-gray-800"
                        >
                          {`${user.first_name || ""} ${user.last_name || ""}`.trim() ||
                            user.email_address ||
                            "Unknown User"}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <Typography.Text>No one assigned</Typography.Text>
                  )}
                </TaskInfoRow>
              </div>
            </div>

            {/* Divider for separation */}
            <Divider />

            {/* Task Input Section */}
            <div>
              <div className="flex flex-col space-y-4">
                {renderTaskInput()}

                <div className="space-y-2">
                  <div className="text-sm font-medium text-gray-700">
                    Comment (Optional)
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
          <Space>
            <Button onClick={handleCancel} disabled={isLoading}>
              Cancel
            </Button>
            <Button
              type="primary"
              onClick={handleSave}
              loading={isLoading}
              disabled={task.input_type === "string" && !textValue.trim()}
            >
              Save
            </Button>
          </Space>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
