import {
  AntButton as Button,
  AntForm as Form,
  AntInput as Input,
  AntModal as Modal,
  AntTypography as Typography,
  useToast,
} from "fidesui";
import { useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";

import { useCreateExternalUserMutation } from "./external-user.slice";

const { Paragraph } = Typography;

interface CreateExternalUserModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUserCreated: () => void;
}

interface FormData {
  email_address: string;
  first_name: string;
  last_name: string;
}

const CreateExternalUserModal = ({
  isOpen,
  onClose,
  onUserCreated,
}: CreateExternalUserModalProps) => {
  const [form] = Form.useForm<FormData>();
  const [isLoading, setIsLoading] = useState(false);
  const [createExternalUser] = useCreateExternalUserMutation();
  const toast = useToast();

  const generateUsername = (email: string) => {
    // Generate username from email address (part before @)
    const username = email.split("@")[0];
    // Sanitize username to only allow alphanumeric characters and underscores
    return username.replace(/[^a-zA-Z0-9_]/g, "_");
  };

  const handleSubmit = async (values: FormData) => {
    setIsLoading(true);
    try {
      const username = generateUsername(values.email_address);

      const result = await createExternalUser({
        username,
        email_address: values.email_address,
        first_name: values.first_name,
        last_name: values.last_name,
      });

      if (isErrorResult(result)) {
        toast(errorToastParams(getErrorMessage(result.error)));
        return;
      }

      toast(
        successToastParams(
          `External respondent user created successfully. The user will receive a welcome email with access instructions.`,
        ),
      );

      form.resetFields();
      onUserCreated();
    } catch (error) {
      toast(
        errorToastParams("Failed to create external user. Please try again."),
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onClose();
  };

  return (
    <Modal
      title="Create External Respondent User"
      open={isOpen}
      onCancel={handleCancel}
      footer={null}
      width={500}
    >
      <div style={{ marginBottom: 16 }}>
        <Paragraph type="secondary">
          Create an external respondent user who can be assigned manual DSR
          tasks. These users access a secure external task portal to complete
          assigned tasks without logging into the Fides admin interface.
        </Paragraph>
        <Paragraph type="secondary">
          If you need to create an internal user that can log in to the Fides
          admin interface, please use the{" "}
          <Typography.Link>Users page</Typography.Link> instead.
        </Paragraph>
      </div>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        requiredMark={false}
      >
        <Form.Item
          name="email_address"
          label="Email Address"
          rules={[
            { required: true, message: "Email address is required" },
            { type: "email", message: "Please enter a valid email address" },
          ]}
        >
          <Input placeholder="user@example.com" />
        </Form.Item>

        <Form.Item
          name="first_name"
          label="First Name"
          rules={[{ required: true, message: "First name is required" }]}
        >
          <Input />
        </Form.Item>

        <Form.Item
          name="last_name"
          label="Last Name"
          rules={[{ required: true, message: "Last name is required" }]}
        >
          <Input />
        </Form.Item>

        <Form.Item style={{ marginBottom: 0, marginTop: 24 }}>
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
            <Button onClick={handleCancel} disabled={isLoading}>
              Cancel
            </Button>
            <Button type="primary" htmlType="submit" loading={isLoading}>
              Create User
            </Button>
          </div>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default CreateExternalUserModal;
