import React from "react";
import { Modal, ModalContent, ModalOverlay } from "@fidesui/react";

type RequestModalProps = {
  isOpen: boolean;
  onClose: () => void;
};

const RequestModal: React.FC<RequestModalProps> = ({
  isOpen,
  onClose,
  children,
}) => (
  <Modal isOpen={isOpen} onClose={onClose}>
    <ModalOverlay />
    <ModalContent top={[0, "205px"]} maxWidth="464px" mx={5} my={3}>
      {children}
    </ModalContent>
  </Modal>
);

export default RequestModal;
