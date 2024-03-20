import {
  Button,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  SimpleGrid,
  Text,
  useDisclosure,
} from "@fidesui/react";

import InfoBox from "~/features/common/InfoBox";
import { useGetPrivacyCenterConfigQuery } from "~/features/privacy-requests/privacy-requests.slice";

const SubmitPrivacyRequestModal = ({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) => {
  const { data } = useGetPrivacyCenterConfigQuery();
  console.log(data);
  const handleSubmit = () => {
    console.log("submitted!");
    onClose();
  };
  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl" isCentered>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Submit privacy request</ModalHeader>
        <ModalBody>
          <InfoBox text="Don't forget, you gotta verify this request." />
          <Text>I am a privacy request, probably.</Text>
        </ModalBody>
        <ModalFooter>
          <SimpleGrid columns={2} width="full">
            <Button variant="outline" size="sm" onClick={onClose} mr={4}>
              Cancel
            </Button>
            <Button colorScheme="primary" size="sm" onClick={handleSubmit}>
              Submit
            </Button>
          </SimpleGrid>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

const SubmitPrivacyRequest = () => {
  const { onOpen, isOpen, onClose } = useDisclosure();
  return (
    <>
      <SubmitPrivacyRequestModal isOpen={isOpen} onClose={onClose} />
      <Button colorScheme="primary" size="sm" onClick={onOpen}>
        Submit request
      </Button>
    </>
  );
};

export default SubmitPrivacyRequest;
