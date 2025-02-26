import { Modal, ModalContent, ModalOverlay } from "fidesui";
import React from "react";

type RequestModalProps = {
  isOpen: boolean;
  onClose: () => void;
  children?: React.ReactNode;
};

const RequestModal = ({ isOpen, onClose, children }: RequestModalProps) => (
  <Modal isOpen={isOpen} onClose={onClose} isCentered>
    <ModalOverlay />
    <ModalContent maxWidth="464px" mx={5} my={3}>
      {children}
    </ModalContent>
  </Modal>
);

export default RequestModal;
