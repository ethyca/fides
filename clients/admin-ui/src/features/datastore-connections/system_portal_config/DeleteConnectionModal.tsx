import {
  Button,
  Flex,
  IconButton,
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
} from "fidesui";
import React from "react";

import { TrashCanSolidIcon } from "~/features/common/Icon/TrashCanSolidIcon";

type DataConnectionProps = {
  onDelete: () => void;
  deleteResult: any;
};

const DeleteConnectionModal = ({
  onDelete,
  deleteResult,
}: DataConnectionProps) => {
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
        <Flex alignItems="center">
          <Text fontSize="sm">Delete integration</Text>
          <IconButton
            marginLeft="8px"
            aria-label="Delete integration"
            variant="outline"
            icon={<TrashCanSolidIcon />}
            isDisabled={deleteResult.isLoading}
            onClick={onOpen}
            size="sm"
          />
        </Flex>
      </>

      <Modal isCentered isOpen={isOpen} onClose={closeIfComplete}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Delete integration</ModalHeader>
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
