import Restrict from "common/Restrict";
import ConnectionListDropdown, {
  useConnectionListDropDown,
} from "datastore-connections/system_portal_config/ConnectionListDropdown";
import OrphanedConnectionModal from "datastore-connections/system_portal_config/OrphanedConnectionModal";
import { AntButton as Button, Box, Flex, Stack, useDisclosure } from "fidesui";
import React, { useEffect, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import ConnectorTemplateUploadModal from "~/features/connector-templates/ConnectorTemplateUploadModal";
import { ConnectorParameters } from "~/features/datastore-connections/system_portal_config/forms/ConnectorParameters";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  ScopeRegistryEnum,
  SystemType,
} from "~/types/api";

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

const ConnectionForm = ({ connectionConfig, systemFidesKey }: Props) => {
  const {
    dropDownOptions,
    selectedValue: selectedConnectionOption,
    setSelectedValue: setSelectedConnectionOption,
  } = useConnectionListDropDown({ connectionConfig });
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
      setOrphanedConnectionConfigs(data.items);
    }
  }, [data]);

  const uploadTemplateModal = useDisclosure();

  /* STEPS TO UNIFY the database and saas forms
  7. Get it working for manual connectors
  8. Add in flow for orphaned connectors
  */

  return (
    <Box id="con-wrapper" px={6}>
      <Flex py={5}>
        <Stack direction={{ base: "column", lg: "row" }}>
          <ConnectionListDropdown
            list={dropDownOptions}
            label="Integration type"
            selectedValue={selectedConnectionOption}
            onChange={setSelectedConnectionOption}
            disabled={Boolean(connectionConfig && connectionConfig !== null)}
          />
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
          </Restrict>
        </Stack>

        <ConnectorTemplateUploadModal
          isOpen={uploadTemplateModal.isOpen}
          onClose={uploadTemplateModal.onClose}
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
