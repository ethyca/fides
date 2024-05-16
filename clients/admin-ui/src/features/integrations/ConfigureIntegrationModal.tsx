import {
  Modal,
  ModalBody,
  ModalContent,
  ModalOverlay,
  Text,
  UseDisclosureReturn,
} from "fidesui";

const ConfigureIntegrationModal = ({
  isOpen,
  onClose,
}: Pick<UseDisclosureReturn, "isOpen" | "onClose">) => (
  <Modal isOpen={isOpen} onClose={onClose} isCentered size="xl">
    <ModalOverlay />
    <ModalContent>
      <ModalBody>
        <Text>hello, modal!</Text>
      </ModalBody>
    </ModalContent>
  </Modal>
);

export default ConfigureIntegrationModal;
