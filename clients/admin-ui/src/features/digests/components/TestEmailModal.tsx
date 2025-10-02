import {
  AntButton as Button,
  AntForm as Form,
  AntInput as Input,
  AntMessage as message,
  AntModal as Modal,
  AntSpace as Space,
} from "fidesui";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { DigestType } from "~/types/api";

import { useTestDigestConfigMutation } from "../digest-config.slice";

interface TestEmailModalProps {
  isOpen: boolean;
  onClose: () => void;
  digestType: DigestType;
}

const TestEmailModal = ({
  isOpen,
  onClose,
  digestType,
}: TestEmailModalProps) => {
  const [form] = Form.useForm<{ email: string }>();
  const [messageApi, messageContext] = message.useMessage();
  const [testDigestConfig, { isLoading }] = useTestDigestConfigMutation();

  const handleSubmit = async (values: { email: string }) => {
    const result = await testDigestConfig({
      digest_config_type: digestType,
      test_email: values.email,
    });

    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
      return;
    }

    messageApi.success(`Test email sent to ${values.email}`);
    form.resetFields();
    onClose();
  };

  const handleCancel = () => {
    form.resetFields();
    onClose();
  };

  return (
    <Modal
      title="Send Test Email"
      open={isOpen}
      onCancel={handleCancel}
      footer={null}
      destroyOnClose
    >
      {messageContext}
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{ email: "" }}
      >
        <Form.Item
          label="Email Address"
          name="email"
          rules={[
            { required: true, message: "Please enter an email address" },
            { type: "email", message: "Please enter a valid email address" },
          ]}
        >
          <Input
            type="email"
            placeholder="user@example.com"
            data-testid="test-email-input"
          />
        </Form.Item>

        <Form.Item>
          <Space className="w-full justify-end">
            <Button onClick={handleCancel} data-testid="cancel-test-btn">
              Cancel
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              loading={isLoading}
              data-testid="send-test-btn"
            >
              Send Test
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default TestEmailModal;
