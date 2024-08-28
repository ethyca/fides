import { useAPIHelper } from "common/hooks";
import { useAlert } from "common/hooks/useAlert";
import {
  selectConnectionTypeState,
  setConnection,
} from "connection-type/connection-type.slice";
import { ConnectionTypeSecretSchemaResponse } from "connection-type/types";
import {
  usePatchDatastoreConnectionMutation,
  useUpdateDatastoreConnectionSecretsMutation,
} from "datastore-connections/datastore-connection.slice";
import { DatastoreConnectionSecretsRequest } from "datastore-connections/types";
import { Box } from "fidesui";
import { useState } from "react";
import { useDispatch } from "react-redux";

import { useAppSelector } from "~/app/hooks";
import {
  AccessLevel,
  ConnectionType,
  CreateConnectionConfigurationWithSecrets,
} from "~/types/api";

import ConnectorParametersForm from "../forms/ConnectorParametersForm";
import { formatKey } from "../helpers";
import {
  BaseConnectorParametersFields,
  DatabaseConnectorParametersFormFields,
} from "../types";

type ConnectorParametersProps = {
  data: ConnectionTypeSecretSchemaResponse;
  /**
   * Parent callback invoked when a connection is initially created
   */
  onConnectionCreated?: () => void;
  /**
   * Parent callback when Test Connection is clicked
   */
  onTestConnectionClick: (value: any) => void;
};

export const useDatabaseConnector = ({
  onConnectionCreated,
  data,
}: Pick<ConnectorParametersProps, "onConnectionCreated" | "data">) => {
  const dispatch = useDispatch();
  const { errorAlert, successAlert } = useAlert();
  const { handleError } = useAPIHelper();

  const [isSubmitting, setIsSubmitting] = useState(false);

  const { connection, connectionOption } = useAppSelector(
    selectConnectionTypeState,
  );

  const [patchDatastoreConnection] = usePatchDatastoreConnectionMutation();
  const [updateDatastoreConnectionSecrets] =
    useUpdateDatastoreConnectionSecretsMutation();

  const handleSubmit = async (values: BaseConnectorParametersFields) => {
    try {
      setIsSubmitting(true);
      const params1: CreateConnectionConfigurationWithSecrets = {
        access: AccessLevel.WRITE,
        connection_type: connectionOption?.identifier as ConnectionType,
        description: values.description,
        disabled: false,
        key: formatKey(values.instance_key as string),
        name: values.name,
      };
      const payload = await patchDatastoreConnection(params1).unwrap();
      if (payload.failed?.length > 0) {
        errorAlert(payload.failed[0].message);
      } else {
        const params2: DatastoreConnectionSecretsRequest = {
          connection_key: payload.succeeded[0].key,
          secrets: {},
        };
        Object.entries(data.properties).forEach((key) => {
          params2.secrets[key[0]] = values[key[0]];
        });
        const payload2 =
          await updateDatastoreConnectionSecrets(params2).unwrap();
        if (payload2.test_status === "failed") {
          errorAlert(
            <>
              <b>Message:</b> {payload2.msg}
              <br />
              <b>Failure Reason:</b> {payload2.failure_reason}
            </>,
          );
        } else {
          dispatch(setConnection(payload.succeeded[0]));
          successAlert(
            `Connector successfully ${connection?.key ? "updated" : "added"}!`,
          );
          if (!connection?.key && onConnectionCreated) {
            onConnectionCreated();
          }
        }
      }
    } catch (error) {
      handleError(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return { isSubmitting, handleSubmit, connectionOption };
};

export const ConnectorParameters = ({
  data,
  onConnectionCreated,
  onTestConnectionClick,
}: ConnectorParametersProps) => {
  const defaultValues = {
    description: "",
    instance_key: "",
    name: "",
  } as DatabaseConnectorParametersFormFields;
  const { isSubmitting, handleSubmit, connectionOption } = useDatabaseConnector(
    { onConnectionCreated, data },
  );

  return (
    <>
      <Box color="gray.700" fontSize="14px" h="80px">
        Connect to your {connectionOption!.human_readable} environment by
        providing the information below. Once you have saved the form, you may
        test the integration to confirm that it&apos;s working correctly.
      </Box>
      <ConnectorParametersForm
        data={data}
        defaultValues={defaultValues}
        isSubmitting={isSubmitting}
        onSaveClick={handleSubmit}
        onTestConnectionClick={onTestConnectionClick}
      />
    </>
  );
};
