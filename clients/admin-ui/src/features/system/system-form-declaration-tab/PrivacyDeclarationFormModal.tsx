import {
  Box,
  Heading,
  Modal,
  ModalBody,
  ModalContent,
  ModalHeader,
  ModalOverlay,
} from "@fidesui/react";

type DataUseFormModalProps = {
  isOpen: boolean;
  onClose: () => void;
  heading: string;
  isCentered?: boolean;
  testId?: string;
  children: React.ReactNode;
};

export const PrivacyDeclarationFormModal: React.FC<DataUseFormModalProps> = ({
  isOpen,
  onClose,
  heading,
  isCentered = false,
  testId = "privacy-declaration-modal",
  children,
}) => (
  <Modal
    isOpen={isOpen}
    onClose={onClose}
    isCentered={isCentered}
    scrollBehavior="inside"
    size="3xl"
  >
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
            {heading}
          </Heading>
        </Box>
      </ModalHeader>
      <ModalBody pb={4}>{children}</ModalBody>
    </ModalContent>
  </Modal>
);
