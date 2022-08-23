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
} from "@fidesui/react";
import React from "react";

import { AccessLevel, ConnectionType } from "./constants";
import { usePatchDatastoreConnectionsMutation } from "./datastore-connection.slice";

type DataConnectionProps = {
  connection_key: string;
  disabled: boolean;
  name: string;
  access_type: AccessLevel;
  connection_type: ConnectionType;
};

const DisableConnectionModal: React.FC<DataConnectionProps> = ({
  connection_key,
  disabled,
  name,
  access_type,
  connection_type,
}) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [patchConnection, patchConnectionResult] =
    usePatchDatastoreConnectionsMutation();

  const handleDisableConnection = async () => {
    const shouldDisable = !disabled;
    patchConnection({
      key: connection_key,
      name,
      disabled: shouldDisable,
      access: access_type,
      connection_type,
    });
  };

  const closeIfComplete = () => {
    if (!patchConnectionResult.isLoading) {
      onClose();
    }
  };

  return (
    <>
      <MenuItem
        _focus={{ color: "complimentary.500", bg: "gray.100" }}
        onClick={onOpen}
      >
        <Text fontSize="sm">{disabled ? "Enable" : "Disable"}</Text>
      </MenuItem>
      <Modal isCentered isOpen={isOpen} onClose={closeIfComplete}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            {disabled ? "Enable" : "Disable"} Connection
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <Stack direction="column" spacing="15px">
              <Text
                color="gray.600"
                fontSize="sm"
                fontWeight="sm"
                lineHeight="20px"
              >
                {disabled ? "Enabling" : "Disabling"} a datastore connection may
                impact any subject request that is currently in progress. Do you
                wish to proceed?
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
              onClick={handleDisableConnection}
              isLoading={patchConnectionResult.isLoading}
              mr={3}
              size="sm"
              variant="solid"
              bg="primary.800"
              color="white"
              width="50%"
            >
              {disabled ? "Enable" : "Disable"} Connection
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};

export default DisableConnectionModal;
