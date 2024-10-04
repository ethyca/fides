import {
  AntButton,
  AntSwitch as Switch,
  Flex,
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

import { ConnectionType } from "~/types/api";

import { AccessLevel } from "./constants";
import { usePatchDatastoreConnectionsMutation } from "./datastore-connection.slice";

type DataConnectionProps = {
  connection_key: string;
  disabled: boolean;
  name: string;
  access_type: AccessLevel;
  connection_type: ConnectionType;
  isSwitch: boolean;
};

const DisableConnectionModal = ({
  connection_key,
  disabled,
  name,
  access_type,
  connection_type,
  isSwitch,
}: DataConnectionProps) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [patchConnection, patchConnectionResult] =
    usePatchDatastoreConnectionsMutation();

  const handleDisableConnection = async () => {
    const shouldDisable = !disabled;
    await patchConnection({
      key: connection_key,
      name,
      disabled: shouldDisable,
      access: access_type,
      connection_type,
    });
    onClose();
  };

  const closeIfComplete = () => {
    if (!patchConnectionResult.isLoading) {
      onClose();
    }
  };

  return (
    <>
      {isSwitch ? (
        <Flex justifyContent="space-between" alignItems="center">
          <Text fontSize="sm">Enable integration</Text>
          <Switch
            className="ml-2"
            checked={!disabled}
            onChange={() => onOpen()}
          />
        </Flex>
      ) : (
        <MenuItem
          _focus={{ color: "complimentary.500", bg: "gray.100" }}
          onClick={onOpen}
        >
          <Text fontSize="sm">{disabled ? "Enable" : "Disable"}</Text>
        </MenuItem>
      )}
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
                {disabled ? "Enabling" : "Disabling"} a connection may impact
                any privacy request that is currently in progress. Do you wish
                to proceed?
              </Text>
            </Stack>
          </ModalBody>

          <ModalFooter className="flex gap-4">
            <AntButton onClick={closeIfComplete} className="w-1/2">
              Cancel
            </AntButton>
            <AntButton
              onClick={handleDisableConnection}
              loading={patchConnectionResult.isLoading}
              className="w-1/2"
            >
              {disabled ? "Enable" : "Disable"} Connection
            </AntButton>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};

export default DisableConnectionModal;
