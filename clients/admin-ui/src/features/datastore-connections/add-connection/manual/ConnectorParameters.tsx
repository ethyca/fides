import { useAPIHelper } from "common/hooks";
import { useAlert } from "common/hooks/useAlert";
import {
  selectConnectionTypeState,
  setConnection,
} from "connection-type/connection-type.slice";
import { usePatchDatastoreConnectionMutation } from "datastore-connections/datastore-connection.slice";
import { Box, Text, VStack } from "fidesui";
import { useState } from "react";
import { useDispatch } from "react-redux";

import { useAppSelector } from "~/app/hooks";
import {
  AccessLevel,
  ConnectionType,
  CreateConnectionConfigurationWithSecrets,
} from "~/types/api";

import { BaseConnectorParametersFields } from "../types";
import ConnectorParametersForm from "./ConnectorParametersForm";

type ConnectorParametersProp = {
  /**
   * Parent callback invoked when a connection is initially created
   */
  onConnectionCreated?: () => void;
};

export const ConnectorParameters = ({
  onConnectionCreated,
}: ConnectorParametersProp) => {
  const dispatch = useDispatch();
  const { errorAlert, successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const defaultValues = {
    description: "",
    name: "",
  } as BaseConnectorParametersFields;
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { connection, connectionOption } = useAppSelector(
    selectConnectionTypeState,
  );

  const [patchDatastoreConnection] = usePatchDatastoreConnectionMutation();

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const handleSubmit = async (values: any, _actions: any) => {
    try {
      setIsSubmitting(true);
      const params: CreateConnectionConfigurationWithSecrets = {
        access: AccessLevel.WRITE,
        connection_type: connectionOption?.identifier as ConnectionType,
        description: values.description,
        disabled: false,
        name: values.name,
        key: connection?.key,
      };
      const payload = await patchDatastoreConnection(params).unwrap();
      if (payload.failed?.length > 0) {
        errorAlert(payload.failed[0].message);
      } else {
        dispatch(setConnection(payload.succeeded[0]));
        successAlert(
          `Connector successfully ${connection?.key ? "updated" : "added"}!`,
        );
        if (!connection?.key && onConnectionCreated) {
          onConnectionCreated();
        }
      }
    } catch (error) {
      handleError(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <VStack align="stretch" gap="16px">
      <Box color="gray.700" fontSize="14px">
        To begin setting up your new {connectionOption!.human_readable}{" "}
        connector you must first assign a name to the connector and a
        description.
        <br />
        <br />
        Once you have completed this section you can then progress onto{" "}
        <Text display="inline-block" fontWeight="700">
          DSR customization
        </Text>{" "}
        using the menu on the left hand side.
      </Box>
      <ConnectorParametersForm
        defaultValues={defaultValues}
        isSubmitting={isSubmitting}
        onSaveClick={handleSubmit}
      />
    </VStack>
  );
};
