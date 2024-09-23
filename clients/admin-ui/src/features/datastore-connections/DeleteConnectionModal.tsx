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
import { useRouter } from "next/router";
import React from "react";

import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";

import { useDeleteDatastoreConnectionMutation } from "./datastore-connection.slice";

type DataConnectionProps = {
  connection_key: string;
  showMenu: boolean;
};

const DeleteConnectionModal = ({
  connection_key,
  showMenu,
}: DataConnectionProps) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [deleteConnection, deleteConnectionResult] =
    useDeleteDatastoreConnectionMutation();
  const router = useRouter();

  const handleDeleteConnection = () => {
    if (connection_key) {
      deleteConnection(connection_key);
      if (!showMenu) {
        router.push(INTEGRATION_MANAGEMENT_ROUTE);
      }
    }
  };

  const closeIfComplete = () => {
    if (!deleteConnectionResult.isLoading) {
      onClose();
    }
  };

  return (
    <>
      {showMenu && (
        <MenuItem
          _focus={{ color: "terracotta", bg: "neutral.100" }}
          onClick={onOpen}
        >
          <Text fontSize="sm">Delete</Text>
        </MenuItem>
      )}
      {!showMenu && <Button onClick={onOpen}>Delete integration</Button>}

      <Modal isCentered isOpen={isOpen} onClose={closeIfComplete}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Delete integration</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <Stack direction="column" spacing="15px">
              <Text
                color="neutral.600"
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
                bg: "neutral.100",
                color: "neutral.600",
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
