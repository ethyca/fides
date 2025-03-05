import {
  AntFlex as Flex,
  AntForm as Form,
  AntInput as Input,
  AntTypography as Typography,
  Button,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalHeader,
  ModalOverlay,
} from "fidesui";
import { useState } from "react";

interface ConsentLookupModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const ConsentLookupModal = ({ isOpen, onClose }: ConsentLookupModalProps) => {
  const [showModal, setShowModal] = useState(false);

  const handleSearch = (value: string) => {
    console.log("value", value);
  };

  return (
    <Modal
      id="custom-field-modal-hello-world"
      isOpen={isOpen}
      onClose={onClose}
      size="6xl"
      returnFocusOnClose={false}
      isCentered
    >
      <ModalOverlay />
      <ModalContent>
        <ModalCloseButton />
        <ModalHeader pb={0}>Consent preference lookup</ModalHeader>
        <ModalBody>
          <Typography.Paragraph>
            Use this search to look up an individual&apos;s latest consent
            record. You can search by phone number, email, or device ID to
            retrieve the most recent consent preference associated with that
            exact identifier.
          </Typography.Paragraph>
          <Typography.Paragraph>
            <strong>Note:</strong> This is an exact match search—partial entries
            or similar results will not be returned. This lookup retrieves only
            the most recent consent preference, not the full consent history.
          </Typography.Paragraph>

          <Form layout="vertical" className="w-1/2">
            <Form.Item label="Subject search" className="mb-4">
              <Input.Search
                data-testid="subject-search-input"
                placeholder="Enter email, phone number, or device ID"
                enterButton="Search"
                onSearch={handleSearch}
              />
            </Form.Item>
          </Form>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};
export default ConsentLookupModal;
