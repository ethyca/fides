import {
  Box,
  Heading,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalContentProps,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  ModalProps,
} from "fidesui";
import { ReactNode } from "react";

interface FormModalProps extends ModalProps {
  title: string;
  children: ReactNode;
  modalContentProps?: ModalContentProps;
  showCloseButton?: boolean;
  footer?: ReactNode;
}

const FormModal = ({
  title,
  children,
  isOpen,
  onClose,
  modalContentProps,
  showCloseButton = false,
  footer,
  ...props
}: FormModalProps) => (
  <Modal
    isOpen={isOpen}
    onClose={onClose}
    isCentered
    scrollBehavior="inside"
    size="xl"
    id="add-modal"
    {...props}
  >
    <ModalOverlay />
    <ModalContent
      textAlign="left"
      p={0}
      data-testid="add-modal-content"
      {...modalContentProps}
    >
      {showCloseButton && <ModalCloseButton />}
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
      <ModalBody pb={4} overflow="auto">
        {children}
      </ModalBody>
      {footer && <ModalFooter>{footer}</ModalFooter>}
    </ModalContent>
  </Modal>
);

export default FormModal;
