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
  onDelete: () => void;
  title: string;
  message: ReactNode;
}
const ConfirmationModal = ({
  isOpen,
  onClose,
  onDelete,
  title,
  message,
}: Props) => (
  <Modal isOpen={isOpen} onClose={onClose} size="lg">
    <ModalOverlay />
    <ModalContent textAlign="center" p={2} data-testid="confirmation-modal">
      <ModalHeader fontWeight="medium">{title}</ModalHeader>
      <ModalBody>{message}</ModalBody>
      <ModalFooter>
        <SimpleGrid columns={2} width="100%">
          <Button
            variant="outline"
            mr={3}
            onClick={onClose}
            data-testid="cancel-btn"
          >
            Cancel
          </Button>
          <Button
            colorScheme="primary"
            onClick={onDelete}
            data-testid="continue-btn"
          >
            Continue
          </Button>
        </SimpleGrid>
      </ModalFooter>
    </ModalContent>
  </Modal>
);

export default ConfirmationModal;
