import {
  Box,
  Heading,
  Modal,
  ModalBody,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  UseDisclosureReturn,
} from "@fidesui/react";
import { ReactNode } from "react";

const AddModal = ({
  title,
  children,
  isOpen,
  onClose,
}: Pick<UseDisclosureReturn, "isOpen" | "onClose"> & {
  title: string;
  children: ReactNode;
}) => (
  <Modal
    isOpen={isOpen}
    onClose={onClose}
    isCentered
    scrollBehavior="inside"
    size="xl"
  >
    <ModalOverlay />
    <ModalContent textAlign="left" p={0}>
      <ModalHeader p={0}>
        <Box
          backgroundColor="gray.50"
          px={6}
          py={4}
          border="1px"
          borderColor="gray.200"
          borderTopRadius={6}
          display="flex"
          justifyContent="space-between"
          alignItems="center"
        >
          <Heading as="h3" size="sm">
            {title}
          </Heading>
        </Box>
      </ModalHeader>
      <ModalBody pb={4} overflow="scroll">
        {children}
      </ModalBody>
    </ModalContent>
  </Modal>
);

export default AddModal;
