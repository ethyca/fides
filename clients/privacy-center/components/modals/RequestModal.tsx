import React from "react";
import { Modal, ModalContent, ModalOverlay } from "fidesui";

type RequestModalProps = {
  isOpen: boolean;
  onClose: () => void;
};

const RequestModal: React.FC<RequestModalProps> = ({
  isOpen,
  onClose,
  children,
}) => (
  <Modal isOpen={isOpen} onClose={onClose} isCentered>
    <ModalOverlay />
    <ModalContent maxWidth="464px" mx={5} my={3}>
      {children}
    </ModalContent>
  </Modal>
);

export default RequestModal;
