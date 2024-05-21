import {
  Modal,
  ModalBody,
  ModalHeader,
  ModalFooter,
  Button,
  ModalContent,
  ModalCloseButton,
  ModalOverlay,
  Text,
  UseDisclosureReturn,
} from "fidesui";

const AddIntegrationModal = ({
  isOpen,
  onClose,
}: Pick<UseDisclosureReturn, "isOpen" | "onClose">) => (
  <Modal isOpen={isOpen} onClose={onClose} isCentered size="xl">
    <ModalOverlay />
    <ModalContent>
        <ModalHeader>Google BigQuery Integration</ModalHeader>
        <ModalCloseButton />
      <ModalBody>
        <Text>Configure integration secret</Text>
        <Text>To connect Fides to BigQuery you must provide an appropriately scoped Secret key. For information on creating a role and secret in GCP read the guide.</Text>
      </ModalBody>
      <ModalFooter>
        <Button colorScheme='blue' mr={3} onClick={onClose}>Cancel</Button>
        <Button variant='ghost'>Connect</Button>
        </ModalFooter>
    </ModalContent>
  </Modal>
);

export default AddIntegrationModal;
