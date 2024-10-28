import {
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  ModalProps,
} from "fidesui";

import TestMessagingProviderConnectionButton, {
  TestMessagingProviderConnectionButtonProps,
} from "./TestMessagingProviderConnectionButton";

export const TestMessagingProviderModal = ({
  serviceType,
  onClose,
  ...props
}: TestMessagingProviderConnectionButtonProps &
  Omit<ModalProps, "children">): JSX.Element => {
  return (
    <Modal isCentered onClose={onClose} {...props}>
      <ModalOverlay />
      <ModalContent data-testid="test-messaging-provider-modal-content">
        <ModalHeader>Test configuration</ModalHeader>
        <ModalCloseButton />
        <ModalBody mb={4}>
          <TestMessagingProviderConnectionButton
            serviceType={serviceType}
            isModal
          />
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};
