import {
  AntButton as Button,
  AntForm as Form,
  AntInput as Input,
  AntSelect as Select,
  AntTooltip as Tooltip,
  Flex,
  Icons,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
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
  key?: string;
  name: string;
  description: string;
  fieldType: ManualTaskFieldType;
  requestType: ManualFieldRequestType;
}

const HelpIcon = ({ text }: { text: string }) => (
  <Tooltip title={text}>
    <Icons.Information
      style={{
        color: palette.FIDESUI_NEUTRAL_500,
        marginLeft: 4,
        cursor: "help",
      }}
    />
  </Tooltip>
);

const AddManualTaskForm = ({
  isSubmitting,
  onSaveClick,
  onCancel,
  editingTask,
}: Props) => {
  const [form] = Form.useForm<TaskFormValues>();

  const isEditing = !!editingTask;

  const requestTypeOptions = [
    { label: "Access", value: ManualFieldRequestType.ACCESS },
    { label: "Erasure", value: ManualFieldRequestType.ERASURE },
  ];

  // Watch request type to determine available field type options
  const requestType = Form.useWatch("requestType", form);

  // Filter field type options based on request type
  const getFieldTypeOptions = () => {
    if (requestType === ManualFieldRequestType.ACCESS) {
      return [
        { label: "Text", value: ManualTaskFieldType.TEXT },
        { label: "Attachment", value: ManualTaskFieldType.ATTACHMENT },
      ];
    }
    if (requestType === ManualFieldRequestType.ERASURE) {
      return [{ label: "Checkbox", value: ManualTaskFieldType.CHECKBOX }];
    }
    // Return empty options when no request type is selected
    return [];
  };

  const fieldTypeOptions = getFieldTypeOptions();
  const isFieldTypeDisabled =
    !requestType || requestType === ManualFieldRequestType.ERASURE;

  // Populate form with existing values when editing
  useEffect(() => {
    if (isEditing && editingTask) {
      form.setFieldsValue({
        key: editingTask.originalField?.key || "",
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
    if (changedValues.requestType !== undefined) {
      // When request type changes to erasure, automatically set field type to checkbox
      if (changedValues.requestType === ManualFieldRequestType.ERASURE) {
        form.setFieldsValue({ fieldType: ManualTaskFieldType.CHECKBOX });
      }
      // When request type changes to access, clear field type if it was checkbox
      else if (changedValues.requestType === ManualFieldRequestType.ACCESS) {
        const currentFieldType = form.getFieldValue("fieldType");
        if (currentFieldType === ManualTaskFieldType.CHECKBOX) {
          form.setFieldsValue({ fieldType: undefined });
        }
      }
      // When request type is cleared, clear field type
      else if (
        changedValues.requestType === null ||
        changedValues.requestType === ""
      ) {
        form.setFieldsValue({ fieldType: undefined });
      }
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
      onValuesChange={handleValuesChange}
      disabled={isSubmitting}
    >
      <Form.Item
        label={
          <div style={{ display: "flex", alignItems: "center" }}>
            Task name
            <HelpIcon text="A clear, descriptive name for this manual task. Example: Export user profile data" />
          </div>
        }
        name="name"
        rules={[
          { required: true, message: "Please enter a task name" },
          { max: 100, message: "Task name must be less than 100 characters" },
        ]}
      >
        <Input placeholder="Enter task name" />
      </Form.Item>

      <Form.Item
        label={
          <div style={{ display: "flex", alignItems: "center" }}>
            Description
            <HelpIcon text="Detailed instructions for completing this task. Example: Download and attach user's profile data from the customer portal" />
          </div>
        }
        name="description"
        rules={[
          { required: true, message: "Please enter a description" },
          { max: 200, message: "Description must be less than 200 characters" },
        ]}
      >
        <Input placeholder="Enter task description" />
      </Form.Item>

      {!isEditing && (
        <Form.Item
          label={
            <div style={{ display: "flex", alignItems: "center" }}>
              Key
              <HelpIcon text="Recommended: Unique identifier for this task that will appear in the DSR package sent to the data subject. If left empty, will be auto-generated from the task name. Example: user_data_export" />
            </div>
          }
          name="key"
          rules={[
            { max: 50, message: "Key must be less than 50 characters" },
            {
              pattern: /^[a-z0-9_]*$/,
              message:
                "Key can only contain lowercase letters, numbers, and underscores",
            },
          ]}
        >
          <Input placeholder="Recommended to specify (auto-generated if empty)" />
        </Form.Item>
      )}

      {isEditing && (
        <Form.Item
          label={
            <div style={{ display: "flex", alignItems: "center" }}>
              Key
              <HelpIcon text="Unique identifier for this task that appears in the DSR package sent to the data subject." />
            </div>
          }
          name="key"
        >
          <Input disabled />
        </Form.Item>
      )}

      <Form.Item
        label={
          <div style={{ display: "flex", alignItems: "center" }}>
            Request type
            <HelpIcon text="Whether this task applies to access requests (providing data) or erasure requests (confirming deletion)" />
          </div>
        }
        name="requestType"
        rules={[{ required: true, message: "Please select a request type" }]}
      >
        <Select
          placeholder="Select request type"
          options={requestTypeOptions}
        />
      </Form.Item>

      <Form.Item
        label={
          <div style={{ display: "flex", alignItems: "center" }}>
            Field type
            <HelpIcon text="Type of input required: Text (for written responses), Attachment (for file uploads), or Checkbox (for confirmation)" />
          </div>
        }
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
          {isEditing ? "Update task" : "Add task"}
        </Button>
      </Flex>
    </Form>
  );
};

export default AddManualTaskForm;
