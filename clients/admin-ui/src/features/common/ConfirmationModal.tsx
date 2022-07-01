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
  title: string;
  message: ReactNode;
}
const ConfirmationModal = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
}: Props) => (
  <Modal isOpen={isOpen} onClose={onClose} size="lg">
    <ModalOverlay />
    <ModalContent textAlign="center" p={2}>
      <ModalHeader fontWeight="medium">{title}</ModalHeader>
      <ModalBody>{message}</ModalBody>
      <ModalFooter>
        <SimpleGrid columns={2} width="100%">
          <Button variant="outline" mr={3} onClick={onClose}>
            Cancel
          </Button>
          <Button colorScheme="primary" onClick={onConfirm}>
            Continue
          </Button>
        </SimpleGrid>
      </ModalFooter>
    </ModalContent>
  </Modal>
);

export default ConfirmationModal;
