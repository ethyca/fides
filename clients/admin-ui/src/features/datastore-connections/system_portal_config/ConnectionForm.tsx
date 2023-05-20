import ConnectionListDropdown, {
  useConnectionListDropDown,
} from "datastore-connections/system_portal_config/ConnectionListDropdown";
import React, { useState, useMemo } from "react";

import { ConnectorParameters } from "~/features/datastore-connections/system_portal_config/forms/ConnectorParameters";
import { SaasForm } from "~/features/datastore-connections/system_portal_config/forms/saas/SaasForm";
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
    systemType,
  } = useConnectionListDropDown({ connectionConfig });

  // If there is a connection load the correct form based on the type
  // If not connection show dropdown that isn't linked to a form.
  // when an option is selected load the correct form
  // if a new option is selected reload the form even if same type

  // eventually give option to select a connection from orphaned connection list
  // if there are any orphaned connections

  // TODO: look into creating new system_connections endpoints for other calls like the secrets one

  /* STEPS TO UNIFY the database and saas forms
  2: Pass the SystemType into the Forms. Use that type to determine if the saas creation endpoint is needed
    2.5: Test that creating/editing saas and database connectors works as expected
  4. Profit
  5. Add dataset configuration to both. If each type requires different behavior account for it.
  6. Get it working for manual connectors
  7. Get it working for email connectors
  8. Add in flow for orphaned connectors
  */

  console.log(systemType, selectedConnectionOption);
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
