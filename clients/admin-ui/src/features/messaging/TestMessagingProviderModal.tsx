import {
  AntButton as Button,
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

import { messagingProviderLabels, messagingProviders } from "./constants";
import { useCreateTestConnectionMessageMutation } from "./messaging.slice";

interface TestMessagingProviderModalProps {
  serviceType: string;
  isOpen: boolean;
  onClose: () => void;
}

export const TestMessagingProviderModal = ({
  serviceType,
  isOpen,
  onClose,
}: TestMessagingProviderModalProps) => {
  const [createTestMessage] = useCreateTestConnectionMessageMutation();
  const [isLoading, setIsLoading] = useState(false);

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

  const handleTestConnection = async () => {
    setIsLoading(true);
    try {
      const isSMSProvider = serviceType === messagingProviders.twilio_text;

      const result = await createTestMessage({
        service_type: serviceType,
        details: {
          to_identity: isSMSProvider
            ? { phone_number: "+15551234567" }
            : { email: "test@example.com" },
        },
      });

      if (isErrorResult(result)) {
        message.error(getErrorMessage(result.error));
      } else {
        message.success("Test message sent successfully!");
        onClose();
      }
    } catch (error) {
      message.error(getErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  };

  const providerLabel =
    messagingProviderLabels[
      serviceType as keyof typeof messagingProviderLabels
    ] || serviceType;

  const isSMSProvider = serviceType === messagingProviders.twilio_text;
  const messageType = isSMSProvider ? "SMS" : "email";

  return (
    <Modal
      title="Test messaging configuration"
      open={isOpen}
      onCancel={onClose}
      footer={[
        <Button key="cancel" onClick={onClose} disabled={isLoading}>
          Cancel
        </Button>,
        <Button
          key="test"
          type="primary"
          onClick={handleTestConnection}
          loading={isLoading}
        >
          Send test {messageType}
        </Button>,
      ]}
    >
      <VStack spacing={4}>
        <Text>
          This will send a test {messageType} using your {providerLabel}{" "}
          configuration.
        </Text>
        {isLoading && (
          <VStack spacing={2} py={4}>
            <Spin />
            <Text fontSize="sm">Sending test {messageType}...</Text>
          </VStack>
        )}
      </VStack>
    </Modal>
  );
};
