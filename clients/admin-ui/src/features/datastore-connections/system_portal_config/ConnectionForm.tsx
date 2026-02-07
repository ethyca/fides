import Restrict from "common/Restrict";
import ConnectionListDropdown, {
  useConnectionListDropDown,
} from "datastore-connections/system_portal_config/ConnectionListDropdown";
import OrphanedConnectionModal from "datastore-connections/system_portal_config/OrphanedConnectionModal";
import {
  Button,
  ChakraBox as Box,
  ChakraFlex as Flex,
  ChakraStack as Stack,
  Tooltip,
  useChakraDisclosure as useDisclosure,
} from "fidesui";
import React, { useEffect, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import { useDeleteConnectorTemplateMutation } from "~/features/connector-templates/connector-template.slice";
import ConnectorTemplateUploadModal from "~/features/connector-templates/ConnectorTemplateUploadModal";
import { ConnectorParameters } from "~/features/datastore-connections/system_portal_config/forms/ConnectorParameters";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  ConnectionType,
  ScopeRegistryEnum,
  SystemType,
} from "~/types/api";

import { CUSTOM_INTEGRATION_INDICATOR } from "../constants";
import {
  selectDatastoreConnectionFilters,
  useGetAllDatastoreConnectionsQuery,
} from "../datastore-connection.slice";

export type ConnectionOption = {
  label: string;
  value: ConnectionSystemTypeMap;
};

type Props = {
  connectionConfig?: ConnectionConfigurationResponse | null;
  systemFidesKey: string;
};

// Website integrations have no reason to be linked to systems
const hiddenConnectionTypes = [
  ConnectionType.WEBSITE,
  ConnectionType.TEST_WEBSITE,
];

const ConnectionForm = ({ connectionConfig, systemFidesKey }: Props) => {
  const {
    dropDownOptions,
    selectedValue: selectedConnectionOption,
    setSelectedValue: setSelectedConnectionOption,
  } = useConnectionListDropDown({
    connectionConfig,
    hiddenTypes: hiddenConnectionTypes,
  });
  const filters = useAppSelector(selectDatastoreConnectionFilters);

  const { data } = useGetAllDatastoreConnectionsQuery({
    ...filters,
    orphaned_from_system: true,
  });
  const [orphanedConnectionConfigs, setOrphanedConnectionConfigs] = useState<
    ConnectionConfigurationResponse[]
  >([]);

  useEffect(() => {
    if (data) {
      // Filter out website connections from orphaned connections since they
      // have no reason to be linked to systems
      const filteredOrphanedConnections = data.items.filter(
        (config) => !hiddenConnectionTypes.includes(config.connection_type),
      );
      setOrphanedConnectionConfigs(filteredOrphanedConnections);
    }
  }, [data]);

  const uploadTemplateModal = useDisclosure();
  const deleteTemplateModal = useDisclosure();
  const [deleteConnectorTemplate, { isLoading: isDeleting }] =
    useDeleteConnectorTemplateMutation();

  const handleDeleteCustomIntegration = async () => {
    if (selectedConnectionOption?.identifier) {
      try {
        await deleteConnectorTemplate(
          selectedConnectionOption.identifier,
        ).unwrap();
        deleteTemplateModal.onClose();
      } catch {
        // Error handling is managed by RTK Query
      }
    }
  };

  /* STEPS TO UNIFY the database and saas forms
  7. Get it working for manual connectors
  8. Add in flow for orphaned connectors
  */

  return (
    <Box id="con-wrapper" px={6}>
      <Flex py={5}>
        <Stack direction={{ base: "column", lg: "row" }} alignItems="center">
          <ConnectionListDropdown
            list={dropDownOptions}
            label="Integration type"
            selectedValue={selectedConnectionOption}
            onChange={setSelectedConnectionOption}
            disabled={Boolean(connectionConfig && connectionConfig !== null)}
          />
          {selectedConnectionOption?.custom && (
            <Tooltip title="Custom integration" placement="top">
              <Box as="span" cursor="pointer" fontSize="lg">
                {CUSTOM_INTEGRATION_INDICATOR}
              </Box>
            </Tooltip>
          )}
          {!connectionConfig && orphanedConnectionConfigs.length > 0 ? (
            <OrphanedConnectionModal
              connectionConfigs={orphanedConnectionConfigs}
              systemFidesKey={systemFidesKey}
            />
          ) : null}

          <Restrict scopes={[ScopeRegistryEnum.CONNECTOR_TEMPLATE_REGISTER]}>
            <Button
              htmlType="submit"
              data-testid="upload-btn"
              onClick={uploadTemplateModal.onOpen}
              className="ml-2"
            >
              Upload integration
            </Button>
            {connectionConfig &&
              selectedConnectionOption?.custom &&
              selectedConnectionOption?.default_connector_available && (
                <Button
                  danger
                  data-testid="delete-custom-integration-btn"
                  onClick={deleteTemplateModal.onOpen}
                  className="ml-2"
                >
                  Delete custom integration
                </Button>
              )}
          </Restrict>
        </Stack>

        <ConnectorTemplateUploadModal
          isOpen={uploadTemplateModal.isOpen}
          onClose={uploadTemplateModal.onClose}
        />
        <ConfirmationModal
          isOpen={deleteTemplateModal.isOpen}
          onClose={deleteTemplateModal.onClose}
          onConfirm={handleDeleteCustomIntegration}
          title="Delete custom integration"
          message="Deleting this custom integration will update all connections that use it by falling back to the Fides-provided template. Are you sure you want to proceed?"
          cancelButtonText="No"
          continueButtonText="Yes"
          isLoading={isDeleting}
          testId="delete-custom-integration-modal"
        />
      </Flex>
      {selectedConnectionOption?.type &&
      [
        SystemType.DATABASE,
        SystemType.DATA_CATALOG,
        SystemType.SAAS,
        SystemType.MANUAL,
        SystemType.EMAIL,
      ].includes(selectedConnectionOption.type) ? (
        <ConnectorParameters
          connectionConfig={connectionConfig}
          connectionOption={selectedConnectionOption}
          setSelectedConnectionOption={setSelectedConnectionOption}
          systemFidesKey={systemFidesKey}
        />
      ) : null}
    </Box>
  );
};

export default ConnectionForm;
