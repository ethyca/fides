// eslint-disable-next-line import/no-extraneous-dependencies
import { ThemingProps } from "@chakra-ui/system";
import {
  Button,
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
  title?: string;
  message?: ReactNode;
  cancelButtonText?: string;
  cancelButtonThemingProps?: ThemingProps<"Button">;
  continueButtonText?: string;
  continueButtonThemingProps?: ThemingProps<"Button">;
  isLoading?: boolean;
  returnFocusOnClose?: boolean;
  isCentered?: boolean;
}
const ConfirmationModal = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  cancelButtonText,
  cancelButtonThemingProps,
  continueButtonText,
  continueButtonThemingProps,
  isLoading,
  returnFocusOnClose,
  isCentered,
}: Props) => (
  <Modal
    isOpen={isOpen}
    onClose={onClose}
    size="lg"
    returnFocusOnClose={returnFocusOnClose || true}
    isCentered={isCentered}
  >
    <ModalOverlay />
    <ModalContent textAlign="center" p={2} data-testid="confirmation-modal">
      {title ? <ModalHeader fontWeight="medium">{title}</ModalHeader> : null}
      {message ? <ModalBody>{message}</ModalBody> : null}
      <ModalFooter>
        <SimpleGrid columns={2} width="100%">
          <Button
            variant="outline"
            mr={3}
            onClick={onClose}
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
