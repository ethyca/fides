import {
  AntButton,
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
            <AntButton onClick={closeIfComplete} className="w-1/2">
              Cancel
            </AntButton>
            <AntButton
              onClick={handleDeleteConnection}
              loading={deleteResult.isLoading}
              type="primary"
              className="w-1/2"
            >
              Delete integration
            </AntButton>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};

export default DeleteConnectionModal;
