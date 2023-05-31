import { Button,Flex, Spacer, useDisclosure } from "@fidesui/react";
import Restrict from "common/Restrict";
import ConnectionListDropdown, {
  useConnectionListDropDown,
} from "datastore-connections/system_portal_config/ConnectionListDropdown";
import React from "react";

import ConnectorTemplateUploadModal from "~/features/connector-templates/ConnectorTemplateUploadModal";
import { ConnectorParameters } from "~/features/datastore-connections/system_portal_config/forms/ConnectorParameters";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  ScopeRegistryEnum,
  SystemType,
} from "~/types/api";

export type ConnectionOption = {
  label: string;
  value: ConnectionSystemTypeMap;
};

type Props = {
  connectionConfig?: ConnectionConfigurationResponse;
  systemFidesKey: string;
};

const ConnectionForm = ({ connectionConfig, systemFidesKey }: Props) => {
  const {
    dropDownOptions,
    selectedValue: selectedConnectionOption,
    setSelectedValue,
  } = useConnectionListDropDown({ connectionConfig });
  const { isOpen, onOpen, onClose } = useDisclosure();

  /* STEPS TO UNIFY the database and saas forms
  7. Get it working for manual connectors
  8. Add in flow for orphaned connectors
  */

  return (
    <>
      <Flex>
        <ConnectionListDropdown
          list={dropDownOptions}
          label="Connection Type"
          selectedValue={selectedConnectionOption}
          onChange={setSelectedValue}
        />
        <Spacer />

        <Restrict scopes={[ScopeRegistryEnum.CONNECTOR_TEMPLATE_REGISTER]}>
          <Button
            colorScheme="primary"
            type="submit"
            minWidth="auto"
            data-testid="upload-btn"
            size="sm"
            onClick={onOpen}
          >
            Upload connector
          </Button>
        </Restrict>
        <ConnectorTemplateUploadModal isOpen={isOpen} onClose={onClose} />
      </Flex>

      {selectedConnectionOption?.type === SystemType.DATABASE ? (
        <ConnectorParameters
          connectionConfig={connectionConfig}
          connectionOption={selectedConnectionOption}
          systemFidesKey={systemFidesKey}
        />
      ) : null}
      {selectedConnectionOption?.type === SystemType.SAAS &&
      selectedConnectionOption ? (
        <ConnectorParameters
          connectionOption={selectedConnectionOption}
          connectionConfig={connectionConfig}
          systemFidesKey={systemFidesKey}
        />
      ) : null}
      {selectedConnectionOption?.type === SystemType.MANUAL &&
      selectedConnectionOption
        ? "Manual Form"
        : null}
      {selectedConnectionOption?.type === SystemType.EMAIL &&
      selectedConnectionOption ? (
        <ConnectorParameters
          connectionOption={selectedConnectionOption}
          connectionConfig={connectionConfig}
          systemFidesKey={systemFidesKey}
        />
      ) : null}
    </>
  );
};

export default ConnectionForm;
