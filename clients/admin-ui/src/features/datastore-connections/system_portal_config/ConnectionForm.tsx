import { Box, Heading, Text, VStack } from "@fidesui/react";
import React, { useMemo, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import DataTabs, { TabData } from "~/features/common/DataTabs";
import {
  reset,
  selectConnectionTypeState,
  setStep,
  setConnectionOption,
} from "~/features/connection-type";

import { ConnectorParameters } from "../add-connection/ConnectorParameters";
import {
  ConfigurationSettings,
  CONNECTOR_PARAMETERS_OPTIONS,
  STEPS,
} from "../add-connection/constants";
import DatasetConfiguration from "../add-connection/DatasetConfiguration";
import DSRCustomization from "../add-connection/manual/DSRCustomization";
import { ConnectorParameterOption } from "../add-connection/types";
import ConnectionTypeLogo from "../ConnectionTypeLogo";
import ConnectionList from "datastore-connections/system_portal_config/ConnectionList";
import { Form, Formik } from "formik";
import { Option } from "common/form/inputs";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  SystemType,
} from "~/types/api";

import { DatabaseForm } from "~/features/datastore-connections/system_portal_config/forms/database/DatabaseForm";

export type ConnectionOption = {
  label: string;
  value: ConnectionSystemTypeMap;
};

type Props = {
  connectionConfig?: ConnectionConfigurationResponse;
  systemFidesKey: string;
};

const ConnectionForm = ({ connectionConfig, systemFidesKey }: Props) => {
  const dispatch = useAppDispatch();

  const [connectionOption, setConnectionOption] =
    useState<ConnectionSystemTypeMap>();
  const [connectorType, setConnectorType] =
    useState<ConnectorParameterOption>();
  // const { connectionOption } = useAppSelector(selectConnectionTypeState);

  const onConnectionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const changeData = JSON.parse(e.target.value) as ConnectionSystemTypeMap
    const item = CONNECTOR_PARAMETERS_OPTIONS.find(
      (o) => o.type === changeData.type
    );
    if (item) {
      setConnectorType(item);
      // dispatch(setConnectionOption(e.value));
      setConnectionOption(changeData);
      console.log("Setting connection", item);
    }
  };

  // TODO: cleanup connectionOption from redux store on component unmount
  console.log(connectionConfig, connectionOption);
  // If there is a connection load the correct form based on the type
  // If not connection show dropdown that isn't linked to a form.
  // when an option is selected load the correct form
  // if a new option is selected reload the form even if same type

  //eventually give option to select a connection from orphaned connection list
  // if there are any orphaned connections


  // TODO: update API calls to use system_connection GET and PATCH
  // TODO: look into creating new system_connections endpoints for other calls like the secrets one
  return (
    <>
      <ConnectionList onChange={onConnectionChange} />
      {connectionOption?.type == SystemType.DATABASE ? (
        <DatabaseForm connectionOption={connectionOption} systemFidesKey={systemFidesKey} />
      ) : null}
      {connectionOption?.type == SystemType.SAAS ? (
        "Saas Form"
      ) : null}
      {connectionOption?.type == SystemType.MANUAL ? (
        "Manual Form"
      ) : null}
      {connectionOption?.type == SystemType.EMAIL ? (
        "Email Form"
      ) : null}
    </>
  );
};

export default ConnectionForm;
