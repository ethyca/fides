import { useAlert, useAPIHelper } from "common/hooks";
import ConnectionTypeLogo from "datastore-connections/ConnectionTypeLogo";
import { ConnectionConfigFormValues } from "datastore-connections/system_portal_config/types";
import {
  AntButton,
  Box,
  Flex,
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
import React, { useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import {
  selectConnectionTypeFilters,
  useGetAllConnectionTypesQuery,
} from "~/features/connection-type";
import { usePatchSystemConnectionConfigsMutation } from "~/features/system";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  ConnectionType,
} from "~/types/api";

import { patchConnectionConfig } from "./forms/ConnectorParameters";

type DataConnectionProps = {
  connectionConfigs: ConnectionConfigurationResponse[];
  systemFidesKey: string;
};

const OrphanedConnectionModal = ({
  connectionConfigs,
  systemFidesKey,
}: DataConnectionProps) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [selectedConnectionConfig, setSelectedConnectionConfig] =
    useState<ConnectionConfigurationResponse | null>(null);

  const { successAlert } = useAlert();

  const [patchDatastoreConnection, { isLoading }] =
    usePatchSystemConnectionConfigsMutation();

  const filters = useAppSelector(selectConnectionTypeFilters);
  const { data } = useGetAllConnectionTypesQuery(filters);

  const connectionOptions = useMemo(() => data?.items || [], [data]);
  const { handleError } = useAPIHelper();
  const closeIfComplete = () => {
    if (isLoading) {
      return;
    }
    if (selectedConnectionConfig) {
      setSelectedConnectionConfig(null);
    }
    onClose();
  };

  const handleLinkingConnection = async () => {
    try {
      if (selectedConnectionConfig) {
        // This is reusing the patchConnectionConfig function from ConnectorParameters.tsx
        // It's being reused in this context since it's a temporary migration step.
        // The function is used in a form in the other context so this needs to be passed in.
        const formValues = {
          ...selectedConnectionConfig,
          instance_key:
            selectedConnectionConfig.connection_type === ConnectionType.SAAS
              ? (selectedConnectionConfig.saas_config?.fides_key as string)
              : selectedConnectionConfig.key,
        } as ConnectionConfigFormValues;

        const connectionOption = connectionOptions.find(
          (ct) =>
            (selectedConnectionConfig?.saas_config &&
              ct.identifier === selectedConnectionConfig?.saas_config.type) ||
            ct.identifier === selectedConnectionConfig?.connection_type,
        ) as ConnectionSystemTypeMap;

        const response = await patchConnectionConfig(
          formValues,
          connectionOption,
          systemFidesKey,
          selectedConnectionConfig,
          patchDatastoreConnection,
        );

        if (response.succeeded[0]) {
          successAlert(`Integration successfully linked!`);
        }

        setSelectedConnectionConfig(null);
        onClose();
      }
    } catch (e) {
      handleError(e);
    }
  };

  return (
    <>
      <AntButton onClick={onOpen}>Link integration</AntButton>

      <Modal isCentered isOpen={isOpen} size="lg" onClose={closeIfComplete}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Unlinked Integrations</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <Stack direction="column" spacing="15px">
              <Text
                color="gray.600"
                fontSize="sm"
                fontWeight="sm"
                lineHeight="20px"
              >
                These are all the integrations that are not linked to a system.
                Please select an integration to link to a system.
              </Text>
              <Box maxHeight="350px" height="100%" overflowY="auto">
                {connectionConfigs.map((connectionConfig) => (
                  <Flex
                    flexDirection="row"
                    key={connectionConfig.key}
                    alignItems="center"
                    _hover={{
                      bg: "gray.100",
                      color: "gray.600",
                    }}
                    bg={
                      selectedConnectionConfig?.key === connectionConfig.key
                        ? "gray.100"
                        : "unset"
                    }
                    color={
                      selectedConnectionConfig?.key === connectionConfig.key
                        ? "gray.600"
                        : "unset"
                    }
                    cursor="pointer"
                    onClick={() => {
                      setSelectedConnectionConfig(connectionConfig);
                    }}
                  >
                    <ConnectionTypeLogo data={connectionConfig} />
                    <Text>{connectionConfig.name}</Text>
                  </Flex>
                ))}
              </Box>
            </Stack>
          </ModalBody>

          <ModalFooter className="flex gap-4">
            <AntButton onClick={closeIfComplete} className="w-1/2">
              Cancel
            </AntButton>
            <AntButton
              onClick={handleLinkingConnection}
              loading={isLoading}
              disabled={!selectedConnectionConfig || isLoading}
              className="w-1/2"
            >
              Link integration
            </AntButton>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};

export default OrphanedConnectionModal;
