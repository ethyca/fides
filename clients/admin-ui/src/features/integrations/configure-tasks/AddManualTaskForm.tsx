import {
  AntButton as Button,
  AntForm as Form,
  AntInput as Input,
  AntSelect as Select,
  Flex,
} from "fidesui";
import React from "react";

import { ManualFieldRequestType, ManualTaskFieldType } from "~/types/api";

type Props = {
  isSubmitting: boolean;
  onSaveClick: (values: any) => void;
  onCancel: () => void;
};

interface TaskFormValues {
  name: string;
  description: string;
  fieldType: ManualTaskFieldType;
  requestType: ManualFieldRequestType;
}

const AddManualTaskForm = ({ isSubmitting, onSaveClick, onCancel }: Props) => {
  const [form] = Form.useForm<TaskFormValues>();

  const fieldTypeOptions = [
    { label: "Text", value: ManualTaskFieldType.TEXT },
    { label: "Checkbox", value: ManualTaskFieldType.CHECKBOX },
    { label: "Attachment", value: ManualTaskFieldType.ATTACHMENT },
  ];

  const requestTypeOptions = [
    { label: "Access", value: ManualFieldRequestType.ACCESS },
    { label: "Erasure", value: ManualFieldRequestType.ERASURE },
  ];

  const handleSubmit = async (values: TaskFormValues) => {
    onSaveClick(values);
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
      disabled={isSubmitting}
    >
      <Form.Item
        label="Task Name"
        name="name"
        rules={[
          { required: true, message: "Please enter a task name" },
          { max: 100, message: "Task name must be less than 100 characters" },
        ]}
      >
        <Input placeholder="Enter task name" />
      </Form.Item>

      <Form.Item
        label="Description"
        name="description"
        rules={[
          { required: true, message: "Please enter a description" },
          { max: 200, message: "Description must be less than 200 characters" },
        ]}
      >
        <Input placeholder="Enter task description" />
      </Form.Item>

      <Form.Item
        label="Field Type"
        name="fieldType"
        rules={[{ required: true, message: "Please select a field type" }]}
      >
        <Select placeholder="Select field type" options={fieldTypeOptions} />
      </Form.Item>

      <Form.Item
        label="Request Type"
        name="requestType"
        rules={[{ required: true, message: "Please select a request type" }]}
      >
        <Select
          placeholder="Select request type"
          options={requestTypeOptions}
        />
      </Form.Item>

      <Flex justify="flex-end" gap={2}>
        <Button onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button type="primary" htmlType="submit" loading={isSubmitting}>
          Add Task
        </Button>
      </Flex>
    </Form>
  );
};

export default AddManualTaskForm;
