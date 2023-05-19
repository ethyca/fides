import ConnectionList from "datastore-connections/system_portal_config/ConnectionList";
import React, { useState } from "react";

import { DatabaseForm } from "~/features/datastore-connections/system_portal_config/forms/database/DatabaseForm";
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
  const [connectionOption, setConnectionOption] =
    useState<ConnectionSystemTypeMap>();

  const onConnectionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const changeData = JSON.parse(e.target.value) as ConnectionSystemTypeMap;
    setConnectionOption(changeData);
  };

  // If there is a connection load the correct form based on the type
  // If not connection show dropdown that isn't linked to a form.
  // when an option is selected load the correct form
  // if a new option is selected reload the form even if same type

  // eventually give option to select a connection from orphaned connection list
  // if there are any orphaned connections

  // TODO: fic the dropdown

  // TODO: look into creating new system_connections endpoints for other calls like the secrets one
  return (
    <>
      <ConnectionList
        onChange={onConnectionChange}
        connectionConfig={connectionConfig}
      />
      {connectionOption?.type === SystemType.DATABASE ? (
        <DatabaseForm
          connectionConfig={connectionConfig}
          connectionOption={connectionOption}
          systemFidesKey={systemFidesKey}
        />
      ) : null}
      {connectionOption?.type === SystemType.SAAS ? "Saas Form" : null}
      {connectionOption?.type === SystemType.MANUAL ? "Manual Form" : null}
      {connectionOption?.type === SystemType.EMAIL ? "Email Form" : null}
    </>
  );
};

export default ConnectionForm;
