import React from "react";
import { Modal, ModalContent, ModalOverlay } from "@fidesui/react";

const NoticeEmptyStateModal = ({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) => (
  <Modal isOpen={isOpen} onClose={onClose}>
    <ModalOverlay />
    <ModalContent top={[0, "205px"]} maxWidth="464px" mx={5} my={3}>
      asdf
    </ModalContent>
  </Modal>
);

export default NoticeEmptyStateModal;
