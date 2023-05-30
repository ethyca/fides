import ConnectionListDropdown, {
  useConnectionListDropDown,
} from "datastore-connections/system_portal_config/ConnectionListDropdown";
import React from "react";

import { ConnectorParameters } from "~/features/datastore-connections/system_portal_config/forms/ConnectorParameters";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
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

  /* STEPS TO UNIFY the database and saas forms
  7. Get it working for manual connectors
  8. Add in flow for orphaned connectors
  */

  return (
    <>
      <ConnectionListDropdown
        list={dropDownOptions}
        label="Connection Type"
        selectedValue={selectedConnectionOption}
        onChange={setSelectedValue}
      />

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
