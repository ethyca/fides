import {
  Button,
  MenuItem,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Stack,
  Text,
  useDisclosure,
} from "fidesui";
import React from "react";

import { useDeleteDatastoreConnectionMutation } from "./datastore-connection.slice";

type DataConnectionProps = {
  connection_key: string;
};

const DeleteConnectionModal = ({ connection_key }: DataConnectionProps) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [deleteConnection, deleteConnectionResult] =
    useDeleteDatastoreConnectionMutation();

  const handleDeleteConnection = () => {
    if (connection_key) {
      deleteConnection(connection_key);
    }
  };

  const closeIfComplete = () => {
    if (!deleteConnectionResult.isLoading) {
      onClose();
    }
  };

  return (
    <>
      <MenuItem
        _focus={{ color: "complimentary.500", bg: "gray.100" }}
        onClick={onOpen}
      >
        <Text fontSize="sm">Delete</Text>
      </MenuItem>
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
              isLoading={deleteConnectionResult.isLoading}
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
