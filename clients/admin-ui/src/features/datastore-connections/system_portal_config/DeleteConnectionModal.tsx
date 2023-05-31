import {
  Button,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Stack,
  Text,
  Spacer,
  useDisclosure,
} from "@fidesui/react";
import React from "react";


type DataConnectionProps = {
  connectionKey: string;
  onDelete: (connection_key: string)=> void;
  deleteResult: any
};

const DeleteConnectionModal: React.FC<DataConnectionProps> = ({
  connectionKey,
  onDelete,
  deleteResult
                                                              }) => {
  const { isOpen, onOpen, onClose } = useDisclosure();


  const handleDeleteConnection = ()=>{
    onDelete(connectionKey)
  }

  const closeIfComplete = () => {
    if (!deleteResult.isLoading && deleteResult.isSuccess) {
      onClose();
    }
  };

  return (
    <>
      <>


        <Spacer/>
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
          <ModalHeader>Delete Connection</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <Stack direction="column" spacing="15px">
              <Text
                color="gray.600"
                fontSize="sm"
                fontWeight="sm"
                lineHeight="20px"
              >
                Deleting a connection may impact any privacy request that is
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
              Delete connection
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};

export default DeleteConnectionModal;
