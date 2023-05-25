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
  5. Add dataset configuration to both. If each type requires different behavior account for it.
  5.1 Add dataset(config) patching to the form submission
  5.2 make sure the dropdown automatically fills in based on the form value
  5.3 Make sure the dropdown works as expected
  5.4 Handles creating and editing well
  5.4 add in yaml modal.
  6. Get it working for manual connectors
  7. Get it working for email connectors
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
      selectedConnectionOption
        ? "Email Form"
        : null}
    </>
  );
};

export default ConnectionForm;
