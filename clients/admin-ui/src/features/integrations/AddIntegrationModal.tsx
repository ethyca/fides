import {
  Button,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
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
        <ModalHeader borderBottom="1px" borderColor="gray.200">Google BigQuery Integration</ModalHeader>
        <ModalCloseButton />
      <ModalBody>
        <Text>Configure integration secret</Text>
        <Text>To connect Fides to BigQuery you must provide an appropriately scoped Secret key. For information on creating a role and secret in GCP read the guide.</Text>
      </ModalBody>
      <ModalFooter>
        <Button
          size="sm"
          variant="outline"
          onClick={onClose}
          mr={2}
          >Cancel</Button>
        <Button
          size="sm"
          variant="primary"
          >Connect</Button>
        </ModalFooter>
    </ModalContent>
  </Modal>
);

export default AddIntegrationModal;
