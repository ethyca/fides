import {
  Button,
  ChakraAlert as Alert,
  ChakraAlertDescription as AlertDescription,
  ChakraAlertIcon as AlertIcon,
  ChakraCode as Code,
  ChakraFlex as Flex,
  ChakraModal as Modal,
  ChakraModalBody as ModalBody,
  ChakraModalContent as ModalContent,
  ChakraModalFooter as ModalFooter,
  ChakraModalHeader as ModalHeader,
  ChakraModalOverlay as ModalOverlay,
  ChakraStack as Stack,
  ChakraText as Text,
  ChakraUseDisclosureReturn as UseDisclosureReturn,
} from "fidesui";

interface ClientSecretModalProps
  extends Pick<UseDisclosureReturn, "isOpen" | "onClose"> {
  clientId: string;
  secret: string;
  /** "created" when shown after initial creation, "rotated" after rotation */
  context: "created" | "rotated";
}

/**
 * Shows the plaintext client secret exactly once — after creation or rotation.
 * The user must close this modal to proceed; there is no way to retrieve the
 * secret again.
 */
const ClientSecretModal = ({
  isOpen,
  onClose,
  clientId,
  secret,
  context,
}: ClientSecretModalProps) => (
  <Modal isOpen={isOpen} onClose={onClose} isCentered size="lg">
    <ModalOverlay />
    <ModalContent data-testid="client-secret-modal">
      <ModalHeader>
        {context === "created" ? "Client created" : "Secret rotated"}
      </ModalHeader>
      <ModalBody>
        <Stack spacing={4}>
          <Alert status="warning" data-testid="secret-warning">
            <AlertIcon />
            <AlertDescription>
              Copy this secret now. It will not be shown again.
            </AlertDescription>
          </Alert>
          <Stack spacing={1}>
            <Text fontSize="sm" fontWeight="medium">
              Client ID
            </Text>
            <Code
              p={2}
              borderRadius="md"
              display="block"
              data-testid="client-id-display"
            >
              {clientId}
            </Code>
          </Stack>
          <Stack spacing={1}>
            <Text fontSize="sm" fontWeight="medium">
              Client secret
            </Text>
            <Code
              p={2}
              borderRadius="md"
              display="block"
              data-testid="client-secret-display"
            >
              {secret}
            </Code>
          </Stack>
        </Stack>
      </ModalBody>
      <ModalFooter>
        <Flex justify="flex-end" w="full">
          <Button type="primary" onClick={onClose} data-testid="done-btn">
            Done
          </Button>
        </Flex>
      </ModalFooter>
    </ModalContent>
  </Modal>
);

export default ClientSecretModal;
