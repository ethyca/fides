import {
  AntButton as Button,
  AntForm as Form,
  AntInput as Input,
  AntModal as Modal,
  AntSpace as Space,
} from "fidesui";
import { useState } from "react";

import { ManualTask } from "~/types/api/models/ManualTask";

import {
  useCompleteTaskMutation,
  useSkipTaskMutation,
} from "../manual-tasks.slice";

interface Props {
  task: ManualTask;
}

export const ActionButtons = ({ task }: Props) => {
  const [completeTask, { isLoading: isCompleting }] = useCompleteTaskMutation();
  const [skipTask, { isLoading: isSkipping }] = useSkipTaskMutation();
  const [isSkipModalOpen, setIsSkipModalOpen] = useState(false);
  const [form] = Form.useForm();

  // Don't render anything for non-new tasks
  if (task.status !== "new") {
    return null;
  }

  const handleComplete = () => {
    completeTask({
      task_id: task.task_id,
      text_value: task.input_type === "string" ? "" : undefined,
      checkbox_value: task.input_type === "checkbox" ? false : undefined,
    });
  };

  const handleSkip = async () => {
    try {
      const values = await form.validateFields();
      await skipTask({
        task_id: task.task_id,
        comment: values.comment,
      });
      setIsSkipModalOpen(false);
      form.resetFields();
    } catch (error) {
      // Form validation failed
    }
  };

  return (
    <Space size="small">
      <Button
        type="primary"
        onClick={handleComplete}
        size="small"
        loading={isCompleting}
      >
        Complete
      </Button>

      <Button
        onClick={() => setIsSkipModalOpen(true)}
        size="small"
        loading={isSkipping}
      >
        Skip
      </Button>

      <Modal
        title="Skip Task"
        open={isSkipModalOpen}
        onOk={handleSkip}
        onCancel={() => {
          setIsSkipModalOpen(false);
          form.resetFields();
        }}
        okText="Skip"
        cancelText="Cancel"
        confirmLoading={isSkipping}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="comment"
            label="Comment"
            rules={[
              {
                required: true,
                message: "Please provide a reason for skipping",
              },
            ]}
          >
            <Input.TextArea
              rows={4}
              placeholder="Why are you skipping this task?"
            />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  );
};
