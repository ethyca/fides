import { Box } from "@fidesui/react";
import { useAPIHelper } from "common/hooks";
import { useAlert } from "common/hooks/useAlert";
import { ConnectionTypeSecretSchemaReponse } from "connection-type/types";
import { useUpdateDatastoreConnectionSecretsMutation } from "datastore-connections/datastore-connection.slice";
import { DatastoreConnectionSecretsRequest } from "datastore-connections/types";
import { useState } from "react";

import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import { usePatchSystemConnectionConfigsMutation } from "~/features/system/system.slice";
import {
  AccessLevel,
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  ConnectionType,
} from "~/types/api";

import {
  BaseConnectorParametersFields,
  DatabaseConnectorParametersFormFields,
} from "../../types";
import ConnectorParametersForm from "../ConnectorParametersForm";

type ConnectorParametersProps = {
  secretsSchema: ConnectionTypeSecretSchemaReponse;
  /**
   * Parent callback when Test Connection is clicked
   */
  onTestConnectionClick: (value: any) => void;
  systemFidesKey: string;
  connectionOption: ConnectionSystemTypeMap;
  connectionConfig?: ConnectionConfigurationResponse;
};

export const useDatabaseConnector = ({
  secretsSchema,
  systemFidesKey,
  connectionOption,
  connectionConfig,
}: Pick<
  ConnectorParametersProps,
  "secretsSchema" | "systemFidesKey" | "connectionOption" | "connectionConfig"
>) => {
  const { errorAlert, successAlert } = useAlert();
  const { handleError } = useAPIHelper();

  const [isSubmitting, setIsSubmitting] = useState(false);

  const [patchDatastoreConnection] = usePatchSystemConnectionConfigsMutation();
  const [updateDatastoreConnectionSecrets] =
    useUpdateDatastoreConnectionSecretsMutation();

  const handleSubmit = async (values: BaseConnectorParametersFields) => {
    try {
      setIsSubmitting(true);
      const params1: Omit<ConnectionConfigurationResponse, "created_at"> = {
        access: AccessLevel.WRITE,
        connection_type: connectionOption?.identifier as ConnectionType,
        description: values.description,
        disabled: false,
        key: formatKey(values.instance_key as string),
        name: values.name,
      };
      const payload = await patchDatastoreConnection({
        systemFidesKey,
        connectionConfigs: [params1],
      }).unwrap();
      if (payload.failed?.length > 0) {
        errorAlert(payload.failed[0].message);
      } else {
        const params2: DatastoreConnectionSecretsRequest = {
          connection_key: payload.succeeded[0].key,
          secrets: {},
        };
        Object.entries(secretsSchema.properties).forEach((key) => {
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
          successAlert(
            `Connector successfully ${
              connectionConfig?.key ? "updated" : "added"
            }!`
          );
        }
      }
    } catch (error) {
      handleError(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return { isSubmitting, handleSubmit };
};

export const DatabaseConnectorParameters: React.FC<
  ConnectorParametersProps
> = ({
  secretsSchema,
  onTestConnectionClick,
  systemFidesKey,
  connectionOption,
  connectionConfig,
}) => {
  const defaultValues = {
    description: "",
    instance_key: "",
    name: "",
  } as DatabaseConnectorParametersFormFields;
  const { isSubmitting, handleSubmit } = useDatabaseConnector({
    secretsSchema,
    systemFidesKey,
    connectionOption,
  });

  return (
    <>
      <Box color="gray.700" fontSize="14px" h="80px">
        Connect to your {connectionOption!.human_readable} environment by
        providing credential information below. Once you have saved your
        connector credentials, you can review what data is included when
        processing a privacy request in your Dataset configuration.
      </Box>
      <ConnectorParametersForm
        data={secretsSchema}
        defaultValues={defaultValues}
        isSubmitting={isSubmitting}
        onSaveClick={handleSubmit}
        onTestConnectionClick={onTestConnectionClick}
        connectionOption={connectionOption}
        connection={connectionConfig}
      />
    </>
  );
};
