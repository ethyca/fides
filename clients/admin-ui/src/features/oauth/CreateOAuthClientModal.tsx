import {
  ChakraModal as Modal,
  ChakraModalBody as ModalBody,
  ChakraModalCloseButton as ModalCloseButton,
  ChakraModalContent as ModalContent,
  ChakraModalHeader as ModalHeader,
  ChakraModalOverlay as ModalOverlay,
  ChakraUseDisclosureReturn as UseDisclosureReturn,
} from "fidesui";

import OAuthClientForm from "./OAuthClientForm";

interface CreateOAuthClientModalProps
  extends Pick<UseDisclosureReturn, "isOpen" | "onClose"> {
  onCreated?: (clientId: string, secret: string) => void;
}

const CreateOAuthClientModal = ({
  isOpen,
  onClose,
  onCreated,
}: CreateOAuthClientModalProps) => (
  <Modal
    isOpen={isOpen}
    onClose={onClose}
    isCentered
    scrollBehavior="inside"
    size="xl"
  >
    <ModalOverlay />
    <ModalContent data-testid="create-oauth-client-modal">
      <ModalHeader>Create API client</ModalHeader>
      <ModalCloseButton />
      <ModalBody pb={6}>
        <OAuthClientForm onClose={onClose} onCreated={onCreated} />
      </ModalBody>
    </ModalContent>
  </Modal>
);

export default CreateOAuthClientModal;
