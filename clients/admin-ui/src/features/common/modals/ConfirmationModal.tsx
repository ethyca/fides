import {
  AntButton as Button,
  Center,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  SimpleGrid,
} from "fidesui";
import { ReactNode } from "react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  onCancel?: () => void;
  title?: string;
  message?: ReactNode;
  cancelButtonText?: string;
  continueButtonText?: string;
  isLoading?: boolean;
  returnFocusOnClose?: boolean;
  isCentered?: boolean;
  testId?: string;
  icon?: ReactNode;
}
const ConfirmationModal = ({
  isOpen,
  onClose,
  onConfirm,
  onCancel,
  title,
  message,
  cancelButtonText,
  continueButtonText,
  isLoading,
  returnFocusOnClose,
  isCentered,
  testId = "confirmation-modal",
  icon,
}: Props) => (
  <Modal
    isOpen={isOpen}
    onClose={onClose}
    size="lg"
    returnFocusOnClose={returnFocusOnClose ?? true}
    isCentered={isCentered}
  >
    <ModalOverlay />
    <ModalContent textAlign="center" p={6} data-testid={testId}>
      {icon ? <Center mb={2}>{icon}</Center> : null}
      {title ? (
        <ModalHeader fontWeight="medium" pb={0}>
          {title}
        </ModalHeader>
      ) : null}
      {message ? <ModalBody>{message}</ModalBody> : null}
      <ModalFooter>
        <SimpleGrid columns={2} width="100%">
          <Button
            onClick={() => {
              if (onCancel) {
                onCancel();
              }
              onClose();
            }}
            size="large"
            className="mr-3"
            data-testid="cancel-btn"
            disabled={isLoading}
          >
            {cancelButtonText || "Cancel"}
          </Button>
          <Button
            type="primary"
            size="large"
            onClick={onConfirm}
            data-testid="continue-btn"
            loading={isLoading}
          >
            {continueButtonText || "Continue"}
          </Button>
        </SimpleGrid>
      </ModalFooter>
    </ModalContent>
  </Modal>
);

export default ConfirmationModal;
