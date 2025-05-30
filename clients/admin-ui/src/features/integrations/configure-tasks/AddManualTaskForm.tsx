import {
  AntButton as Button,
  AntForm as Form,
  AntInput as Input,
  AntSelect as Select,
  Flex,
} from "fidesui";
import React from "react";

import { useGetAllUsersQuery } from "~/features/user-management/user-management.slice";

import { TASK_INPUT_TYPE_OPTIONS, TaskInputType } from "./types";

type Props = {
  isSubmitting: boolean;
  onSaveClick: (values: any) => void;
  onCancel: () => void;
};

interface TaskFormValues {
  name: string;
  description: string;
  types: TaskInputType;
  assignedTo: string[];
}

const AddManualTaskForm = ({ isSubmitting, onSaveClick, onCancel }: Props) => {
  const [form] = Form.useForm<TaskFormValues>();

  // Get users for the assigned to field
  const { data: usersData } = useGetAllUsersQuery({
    page: 1,
    size: 100, // Get enough users for the dropdown
    username: "", // Empty string to get all users
  });

  const users = usersData?.items ?? [];

  // Create options for the assigned to select
  const userOptions = users.map((user: any) => ({
    label: `${user.first_name} ${user.last_name} (${user.email_address})`,
    value: user.email_address,
  }));

  const handleSubmit = async (values: TaskFormValues) => {
    // Add empty data_categories array as required by API and convert types to array
    const formattedValues = {
      name: values.name,
      description: values.description,
      types: [values.types], // Convert single value to array for API
      assignedTo: values.assignedTo || [],
      data_categories: [],
    };
    onSaveClick(formattedValues);
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
        label="Type"
        name="types"
        rules={[{ required: true, message: "Please select a type" }]}
      >
        <Select
          placeholder="Select task type"
          options={TASK_INPUT_TYPE_OPTIONS}
        />
      </Form.Item>

      <Form.Item
        label="Assigned to"
        name="assignedTo"
        help="Select users or enter email addresses"
      >
        <Select
          mode="tags"
          placeholder="Select users or enter email addresses"
          options={userOptions}
          tokenSeparators={[","]}
          filterOption={(input, option) =>
            option?.label?.toLowerCase().includes(input.toLowerCase()) || false
          }
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
