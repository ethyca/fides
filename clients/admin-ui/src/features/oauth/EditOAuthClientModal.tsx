import {
  ChakraModal as Modal,
  ChakraModalBody as ModalBody,
  ChakraModalCloseButton as ModalCloseButton,
  ChakraModalContent as ModalContent,
  ChakraModalHeader as ModalHeader,
  ChakraModalOverlay as ModalOverlay,
  ChakraUseDisclosureReturn as UseDisclosureReturn,
} from "fidesui";

import { ClientResponse } from "~/types/api";

import OAuthClientForm from "./OAuthClientForm";

interface EditOAuthClientModalProps
  extends Pick<UseDisclosureReturn, "isOpen" | "onClose"> {
  client: ClientResponse;
}

const EditOAuthClientModal = ({
  isOpen,
  onClose,
  client,
}: EditOAuthClientModalProps) => (
  <Modal
    isOpen={isOpen}
    onClose={onClose}
    isCentered
    scrollBehavior="inside"
    size="xl"
  >
    <ModalOverlay />
    <ModalContent data-testid="edit-oauth-client-modal">
      <ModalHeader>Edit API client</ModalHeader>
      <ModalCloseButton />
      <ModalBody pb={6}>
        <OAuthClientForm client={client} onClose={onClose} />
      </ModalBody>
    </ModalContent>
  </Modal>
);

export default EditOAuthClientModal;
