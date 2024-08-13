import {
  Button,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Text,
} from "fidesui";

const NoticeEmptyStateModal = ({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) => (
  <Modal isOpen={isOpen} onClose={onClose} isCentered>
    <ModalOverlay />
    <ModalContent textAlign="center" data-testid="notice-empty-state">
      <ModalHeader fontSize="lg" pt={6} fontWeight={500}>
        Consent management unavailable
      </ModalHeader>
      <ModalBody py={0}>
        <Text fontSize="sm" fontWeight={400} color="neutral.500">
          Consent management is unavailable in your area.
        </Text>
      </ModalBody>
      <ModalFooter display="flex" justifyContent="center" py={6}>
        <Button size="sm" colorScheme="neutral" width="100%" onClick={onClose}>
          Ok
        </Button>
      </ModalFooter>
    </ModalContent>
  </Modal>
);

export default NoticeEmptyStateModal;
