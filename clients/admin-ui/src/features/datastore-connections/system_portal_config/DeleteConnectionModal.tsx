import {
  AntButton as Button,
  Flex,
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
          <Button
            aria-label="Delete integration"
            icon={<TrashCanSolidIcon />}
            disabled={deleteResult.isLoading}
            onClick={onOpen}
            className="ml-2"
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
            <Button onClick={closeIfComplete} className="w-1/2">
              Cancel
            </Button>
            <Button
              onClick={handleDeleteConnection}
              loading={deleteResult.isLoading}
              type="primary"
              className="w-1/2"
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
