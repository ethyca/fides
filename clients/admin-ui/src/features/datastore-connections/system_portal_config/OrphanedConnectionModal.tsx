import ConnectionTypeLogo, {
  connectionLogoFromConfiguration,
} from "datastore-connections/ConnectionTypeLogo";
import { ConnectionConfigFormValues } from "datastore-connections/system_portal_config/types";
import {
  Button,
  ChakraBox as Box,
  ChakraFlex as Flex,
  ChakraStack as Stack,
  ChakraText as Text,
  Modal,
  useChakraDisclosure as useDisclosure,
  useMessage,
} from "fidesui";
import React, { useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { useAPIHelper } from "~/features/common/hooks";
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

  const message = useMessage();
  const { handleError } = useAPIHelper();

  const [patchDatastoreConnection, { isLoading }] =
    usePatchSystemConnectionConfigsMutation();

  const filters = useAppSelector(selectConnectionTypeFilters);
  const { data } = useGetAllConnectionTypesQuery(filters);

  const connectionOptions = useMemo(() => data?.items || [], [data]);
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
          message.success(`Integration successfully linked!`);
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
      <Button onClick={onOpen}>Link integration</Button>

      <Modal
        centered
        destroyOnHidden
        open={isOpen}
        onCancel={closeIfComplete}
        title="Unlinked Integrations"
        footer={
          <div className="flex gap-4">
            <Button onClick={closeIfComplete} className="w-1/2">
              Cancel
            </Button>
            <Button
              onClick={handleLinkingConnection}
              loading={isLoading}
              disabled={!selectedConnectionConfig || isLoading}
              className="w-1/2"
            >
              Link integration
            </Button>
          </div>
        }
      >
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
                className="mb-2 hover:bg-gray-100 hover:text-gray-600"
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
                <ConnectionTypeLogo
                  data={connectionLogoFromConfiguration(connectionConfig)}
                  className="mr-2"
                />
                <Text>{connectionConfig.name}</Text>
              </Flex>
            ))}
          </Box>
        </Stack>
      </Modal>
    </>
  );
};

export default OrphanedConnectionModal;
