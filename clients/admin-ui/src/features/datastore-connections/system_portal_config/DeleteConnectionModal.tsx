import {
  Button,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Spacer,
  Stack,
  Text,
  useDisclosure,
} from "@fidesui/react";
import React from "react";

type DataConnectionProps = {
  onDelete: () => void;
  deleteResult: any;
};

const DeleteConnectionModal: React.FC<DataConnectionProps> = ({
  onDelete,
  deleteResult,
}) => {
  const { isOpen, onOpen, onClose } = useDisclosure();

  const handleDeleteConnection = () => {
    onDelete();
  };

  const closeIfComplete = () => {
    if (
      (!deleteResult.isLoading && deleteResult.isSuccess) ||
      (!deleteResult.isLoading && deleteResult.isUninitialized)
    ) {
      onClose();
    }
  };

  return (
    <>
      <>
        <Spacer />
        <Button
          bg="red.500"
          color="white"
          isDisabled={deleteResult.isLoading}
          isLoading={deleteResult.isLoading}
          loadingText="Deleting"
          size="sm"
          variant="solid"
          onClick={onOpen}
          _active={{ bg: "red.400" }}
          _hover={{ bg: "red.300" }}
        >
          Delete
        </Button>
      </>

      <Modal isCentered isOpen={isOpen} onClose={closeIfComplete}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Delete Integration</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <Stack direction="column" spacing="15px">
              <Text
                color="gray.600"
                fontSize="sm"
                fontWeight="sm"
                lineHeight="20px"
              >
                Deleting an integration may impact any privacy request that is
                currently in progress. Do you wish to proceed?
              </Text>
            </Stack>
          </ModalBody>

          <ModalFooter>
            <Button
              onClick={closeIfComplete}
              marginRight="10px"
              size="sm"
              variant="solid"
              bg="white"
              width="50%"
            >
              Cancel
            </Button>
            <Button
              onClick={handleDeleteConnection}
              isLoading={deleteResult.isLoading}
              mr={3}
              size="sm"
              variant="solid"
              bg="primary.800"
              color="white"
              width="50%"
              _loading={{
                opacity: 1,
                div: { opacity: 0.4 },
              }}
              _hover={{
                bg: "gray.100",
                color: "gray.600",
              }}
            >
              Delete integration
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};

export default DeleteConnectionModal;
