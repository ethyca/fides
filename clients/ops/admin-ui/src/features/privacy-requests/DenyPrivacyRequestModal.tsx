import {
  Button,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Textarea,
} from "@fidesui/react";
import React from "react";

type DenyModalProps = {
  isOpen: boolean;
  isLoading: boolean;
  handleMenuClose: () => void;
  handleDenyRequest: (reason: string) => Promise<any>;
  denialReason: string;
  onChange: (e: any) => void;
};

const closeModal = (
  handleMenuClose: () => void,
  handleDenyRequest: (reason: string) => Promise<any>,
  denialReason: string
) => {
  handleDenyRequest(denialReason).then(() => {
    handleMenuClose();
  });
};

const DenyPrivacyRequestModal = ({
  isOpen,
  isLoading,
  handleMenuClose,
  denialReason,
  onChange,
  handleDenyRequest,
}: DenyModalProps) => (
  <Modal
    isOpen={isOpen}
    onClose={handleMenuClose}
    isCentered
    returnFocusOnClose={false}
  >
    <ModalOverlay />
    <ModalContent width="100%" maxWidth="456px">
      <ModalHeader>Data subject request denial</ModalHeader>
      <ModalBody color="gray.500" fontSize="14px">
        Please enter a reason for denying this data subject request. Please
        note: this can be seen by the data subject in their notification email.
      </ModalBody>
      <ModalBody>
        <Textarea
          focusBorderColor="primary.600"
          value={denialReason}
          onChange={onChange}
          disabled={isLoading}
        />
      </ModalBody>
      <ModalFooter>
        <Button
          size="sm"
          width="100%"
          maxWidth="198px"
          colorScheme="gray.200"
          mr={3}
          disabled={isLoading}
          onClick={handleMenuClose}
        >
          Close
        </Button>
        <Button
          size="sm"
          width="100%"
          maxWidth="198px"
          colorScheme="primary"
          variant="solid"
          isLoading={isLoading}
          onClick={() => {
            closeModal(handleMenuClose, handleDenyRequest, denialReason);
          }}
        >
          Confirm
        </Button>
      </ModalFooter>
    </ModalContent>
  </Modal>
);

export default DenyPrivacyRequestModal;
