import {
  Button,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  SimpleGrid,
} from "@fidesui/react";



type Props = {
  isOpen: boolean;
  onClose: () => void;
  isLoading: boolean;
}


export const CustomFieldModal = ({isOpen, onClose, isLoading}: Props)=> {
  return (
    <Modal
    isOpen={isOpen}
    onClose={onClose}
    size="lg"
    returnFocusOnClose={false}
    isCentered
  >
    <ModalOverlay />
    <ModalContent textAlign="center" p={6} data-testid="custom-field-modal">
        <ModalHeader fontWeight="medium" pb={0}>
          Edit Custom Field
        </ModalHeader>
       <ModalBody>Form goes here</ModalBody>
      <ModalFooter>
        <SimpleGrid columns={2} width="100%">
          <Button
            variant="outline"
            mr={3}
            onClick={onClose}
            data-testid="cancel-btn"
            isDisabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            colorScheme="primary"
            // onClick={onConfirm}
            data-testid="save-btn"
            isLoading={isLoading}
          >
           Save
          </Button>
        </SimpleGrid>
      </ModalFooter>
    </ModalContent>
  </Modal>
  )
}