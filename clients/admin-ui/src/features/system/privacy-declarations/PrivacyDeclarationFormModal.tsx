import {
  Box,
  Button,
  Flex,
  Heading,
  HStack,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Spacer,
  Text,
  useToast,
} from "@fidesui/react";

type DataUseFormModalProps = {
  isOpen: boolean;
  onClose: () => void;
  testId?: String;
  children: React.ReactNode;
};

export const PrivacyDeclarationFormModal: React.FC<DataUseFormModalProps> = ({
  isOpen,
  onClose,
  testId = "privacy-declaration-modal",
  children,
}) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose} scrollBehavior="inside" size="3xl">
      <ModalOverlay />
      <ModalContent textAlign="left" p={0} data-testid={testId}>
        <ModalHeader p={0}>
          <Box
            backgroundColor="gray.50"
            px={6}
            py={4}
            border="1px"
            borderColor="gray.200"
            borderTopRadius={6}
          >
            <Heading as="h3" size="sm">
              Configure data use
            </Heading>
          </Box>
        </ModalHeader>
        <ModalBody>
          {children}
          <ModalFooter>
            <Flex w="100%">
              <Button
                variant="outline"
                size="sm"
                onClick={onClose}
                data-testid="cancel-btn"
              >
                Cancel
              </Button>
              <Spacer />
              <Button
                colorScheme="primary"
                size="sm"
                type="submit"
                data-testid="submit-btn"
              >
                Save (nothing yet)
              </Button>
            </Flex>
          </ModalFooter>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};
