import { Box } from "@fidesui/react";
import { useAPIHelper } from "common/hooks";
import { useAlert } from "common/hooks/useAlert";
import {
  selectConnectionTypeState,
  setConnection,
} from "connection-type/connection-type.slice";
import { ConnectionTypeSecretSchemaReponse } from "connection-type/types";
import {
  useCreateSassConnectionConfigMutation,
  usePatchDatastoreConnectionMutation,
  useUpdateDatastoreConnectionSecretsMutation,
} from "datastore-connections/datastore-connection.slice";
import {
  CreateSaasConnectionConfigRequest,
  DatastoreConnectionRequest,
  DatastoreConnectionSecretsRequest,
} from "datastore-connections/types";
import React, { useState } from "react";
import { useDispatch } from "react-redux";

import { useAppSelector } from "~/app/hooks";

import ConnectorParametersForm from "../forms/ConnectorParametersForm";
import { formatKey } from "../helpers";
import { SaasConnectorParametersFormFields } from "../types";

type ConnectorParametersProps = {
  data: ConnectionTypeSecretSchemaReponse;
  /**
   * Parent callback invoked when a connection is initially created
   */
  onConnectionCreated?: () => void;
  /**
   * Parent callback when Test Connection is clicked
   */
  onTestConnectionClick: (value: any) => void;
};

export const ConnectorParameters: React.FC<ConnectorParametersProps> = ({
  data,
  onConnectionCreated,
  onTestConnectionClick,
}) => {
  const dispatch = useDispatch();
  const { errorAlert, successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const defaultValues = {
    description: "",
    instance_key: "",
    name: "",
  } as SaasConnectorParametersFormFields;
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { connection, connectionOption } = useAppSelector(
    selectConnectionTypeState
  );

  const [createSassConnectionConfig] = useCreateSassConnectionConfigMutation();
  const [patchDatastoreConnection] = usePatchDatastoreConnectionMutation();
  const [updateDatastoreConnectionSecrets] =
    useUpdateDatastoreConnectionSecretsMutation();

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const handleSubmit = async (values: any, _actions: any) => {
    try {
      setIsSubmitting(true);
      if (connection) {
        // Update existing Sass connector
        const params1: DatastoreConnectionRequest = {
          access: "write",
          connection_type: connection.connection_type,
          description: values.description,
          disabled: false,
          key: connection.key,
          name: values.name,
        };
        const payload1 = await patchDatastoreConnection(params1).unwrap();
        if (payload1.failed?.length > 0) {
          errorAlert(payload1.failed[0].message);
        } else {
          dispatch(setConnection(payload1.succeeded[0]));
          const params2: DatastoreConnectionSecretsRequest = {
            connection_key: connection.key,
            secrets: {},
          };
          Object.entries(data.properties).forEach((key) => {
            params2.secrets[key[0]] = values[key[0]];
          });
          const payload2 = await updateDatastoreConnectionSecrets(
            params2
          ).unwrap();
          if (payload2.test_status === "failed") {
            errorAlert(
              <>
                <b>Message:</b> {payload2.msg}
                <br />
                <b>Failure Reason:</b> {payload2.failure_reason}
              </>
            );
          } else {
            successAlert(`Connector successfully updated!`);
          }
        }
      } else {
        // Create new Sass connector
        const params: CreateSaasConnectionConfigRequest = {
          description: values.description,
          name: values.name,
          instance_key: formatKey(values.instance_key as string),
          saas_connector_type: connectionOption!.identifier,
          secrets: {},
        };
        Object.entries(data.properties).forEach((key) => {
          params.secrets[key[0]] = values[key[0]];
        });
        const payload = await createSassConnectionConfig(params).unwrap();
        dispatch(setConnection(payload.connection));
        successAlert(`Connector successfully added!`);
        onConnectionCreated?.();
      }
    } catch (error) {
      handleError(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <Box color="gray.700" fontSize="14px" h="80px">
        Connect to your {connectionOption!.human_readable} environment by
        providing credential information below. Once you have saved your
        connector credentials, you can review what data is included when
        processing a privacy request in your Dataset configuration.
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
