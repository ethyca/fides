import {
  AntButton as Button,
  AntForm as Form,
  AntInput as Input,
  AntMessage as message,
  AntModal as Modal,
  AntSpin as Spin,
  Text,
  VStack,
} from "fidesui";
import { useState } from "react";

import {
  isErrorResult,
  isErrorWithDetail,
  isErrorWithDetailArray,
} from "~/features/common/helpers";

import { messagingProviders } from "./constants";
import { useCreateTestConnectionMessageMutation } from "./messaging.slice";

interface SendTestMessageModalProps {
  serviceType: string;
  isOpen: boolean;
  onClose: () => void;
}

export const SendTestMessageModal = ({
  serviceType,
  isOpen,
  onClose,
}: SendTestMessageModalProps) => {
  const [createTestMessage] = useCreateTestConnectionMessageMutation();
  const [isLoading, setIsLoading] = useState(false);
  const [form] = Form.useForm();

  // Helper function to extract error message using the same logic as useAPIHelper
  const getErrorMessage = (error: any) => {
    let errorMsg = "An unexpected error occurred. Please try again.";
    if (isErrorWithDetail(error)) {
      errorMsg = error.data.detail;
    } else if (isErrorWithDetailArray(error)) {
      errorMsg = error.data.detail[0].msg;
    }
    return errorMsg;
  };

  const handleSendTestMessage = async (values: any) => {
    setIsLoading(true);
    try {
      const isSMSProvider = serviceType === messagingProviders.twilio_text;

      const result = await createTestMessage({
        service_type: serviceType,
        details: {
          to_identity: isSMSProvider
            ? { phone_number: values.phone }
            : { email: values.email },
        },
      });

      if (isErrorResult(result)) {
        message.error(getErrorMessage(result.error));
      } else {
        message.success("Test message sent successfully!");
        form.resetFields();
        onClose();
      }
    } catch (error) {
      message.error(getErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  };

  const isSMSProvider = serviceType === messagingProviders.twilio_text;
  const messageType = isSMSProvider ? "SMS" : "email";

  const handleClose = () => {
    form.resetFields();
    onClose();
  };

  return (
    <Modal
      title={`Test ${messageType}`}
      open={isOpen}
      onCancel={handleClose}
      footer={null}
    >
      <VStack spacing={4}>
        <Form
          form={form}
          onFinish={handleSendTestMessage}
          layout="vertical"
          style={{ width: "100%" }}
        >
          {isSMSProvider ? (
            <Form.Item
              name="phone"
              label="Phone number"
              rules={[
                { required: true, message: "Phone number is required" },
                { pattern: /^\+?[1-9]\d{1,14}$/, message: "Please enter a valid phone number" },
              ]}
            >
              <Input placeholder="+1234567890" />
            </Form.Item>
          ) : (
            <Form.Item
              name="email"
              label="Email address"
              rules={[
                { required: true, message: "Email address is required" },
                { type: "email", message: "Please enter a valid email address" },
              ]}
            >
              <Input placeholder="test@example.com" />
            </Form.Item>
          )}

          <Form.Item style={{ marginBottom: 0, marginTop: 24 }}>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}>
              <Button onClick={handleClose} disabled={isLoading}>
                Cancel
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={isLoading}
                data-testid="send-test-message-btn"
              >
                {isLoading ? (
                  <>
                    <Spin size="small" style={{ marginRight: 8 }} />
                    Sending...
                  </>
                ) : (
                  `Send test ${messageType}`
                )}
              </Button>
            </div>
          </Form.Item>
        </Form>
      </VStack>
    </Modal>
  );
};
