import {
  AntButton as Button,
  AntForm as Form,
  AntInput as Input,
  AntSelect as Select,
  Flex,
} from "fidesui";
import React, { useEffect } from "react";

import { ManualFieldRequestType, ManualTaskFieldType } from "~/types/api";

import { Task } from "./useTaskColumns";

type Props = {
  isSubmitting: boolean;
  onSaveClick: (values: any) => void;
  onCancel: () => void;
  editingTask?: Task | null;
};

interface TaskFormValues {
  name: string;
  description: string;
  fieldType: ManualTaskFieldType;
  requestType: ManualFieldRequestType;
}

const AddManualTaskForm = ({
  isSubmitting,
  onSaveClick,
  onCancel,
  editingTask,
}: Props) => {
  const [form] = Form.useForm<TaskFormValues>();

  const isEditing = !!editingTask;

  const fieldTypeOptions = [
    { label: "Text", value: ManualTaskFieldType.TEXT },
    { label: "Checkbox", value: ManualTaskFieldType.CHECKBOX },
    { label: "Attachment", value: ManualTaskFieldType.ATTACHMENT },
  ];

  const requestTypeOptions = [
    { label: "Access", value: ManualFieldRequestType.ACCESS },
    { label: "Erasure", value: ManualFieldRequestType.ERASURE },
  ];

  // Populate form with existing values when editing
  useEffect(() => {
    if (isEditing && editingTask) {
      form.setFieldsValue({
        name: editingTask.name,
        description: editingTask.description,
        fieldType: editingTask.fieldType as ManualTaskFieldType,
        requestType: editingTask.requestType as ManualFieldRequestType,
      });
    } else {
      // Reset form when not editing
      form.resetFields();
    }
  }, [form, isEditing, editingTask]);

  const handleSubmit = async (values: TaskFormValues) => {
    onSaveClick(values);
  };

  const handleValuesChange = (changedValues: Partial<TaskFormValues>) => {
    // When request type changes to erasure, automatically set field type to checkbox
    if (changedValues.requestType === ManualFieldRequestType.ERASURE) {
      form.setFieldsValue({ fieldType: ManualTaskFieldType.CHECKBOX });
    }
  };

  // Watch request type to determine if field type should be disabled
  const requestType = Form.useWatch("requestType", form);
  const isFieldTypeDisabled = requestType === ManualFieldRequestType.ERASURE;

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
      onValuesChange={handleValuesChange}
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
        label="Request Type"
        name="requestType"
        rules={[{ required: true, message: "Please select a request type" }]}
      >
        <Select
          placeholder="Select request type"
          options={requestTypeOptions}
        />
      </Form.Item>

      <Form.Item
        label="Field Type"
        name="fieldType"
        rules={[{ required: true, message: "Please select a field type" }]}
      >
        <Select
          placeholder="Select field type"
          options={fieldTypeOptions}
          disabled={isFieldTypeDisabled}
        />
      </Form.Item>

      <Flex justify="flex-end" gap={2}>
        <Button onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button type="primary" htmlType="submit" loading={isSubmitting}>
          {isEditing ? "Update Task" : "Add Task"}
        </Button>
      </Flex>
    </Form>
  );
};

export default AddManualTaskForm;
