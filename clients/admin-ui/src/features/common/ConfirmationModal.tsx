// eslint-disable-next-line import/no-extraneous-dependencies
import { ThemingProps } from "@chakra-ui/system";
import {
  Button,
  Center,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  SimpleGrid,
} from "@fidesui/react";
import { ReactNode } from "react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  onCancel?: () => void;
  title?: string;
  message?: ReactNode;
  cancelButtonText?: string;
  cancelButtonThemingProps?: ThemingProps<"Button">;
  continueButtonText?: string;
  continueButtonThemingProps?: ThemingProps<"Button">;
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
  cancelButtonThemingProps,
  continueButtonText,
  continueButtonThemingProps,
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
            variant="outline"
            mr={3}
            onClick={() => {
              if (onCancel) {
                onCancel();
              }
              onClose();
            }}
            data-testid="cancel-btn"
            isDisabled={isLoading}
            {...cancelButtonThemingProps}
          >
            {cancelButtonText || "Cancel"}
          </Button>
          <Button
            colorScheme="primary"
            onClick={onConfirm}
            data-testid="continue-btn"
            isLoading={isLoading}
            {...continueButtonThemingProps}
          >
            {continueButtonText || "Continue"}
          </Button>
        </SimpleGrid>
      </ModalFooter>
    </ModalContent>
  </Modal>
);

export default ConfirmationModal;
