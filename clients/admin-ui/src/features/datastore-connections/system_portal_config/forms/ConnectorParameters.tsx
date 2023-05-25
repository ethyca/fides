import { Box, SlideFade } from "@fidesui/react";
import { useAPIHelper } from "common/hooks";
import { useAlert } from "common/hooks/useAlert";
import { ConnectionTypeSecretSchemaReponse } from "connection-type/types";
import {
  CreateSaasConnectionConfig,
  useCreateSassConnectionConfigMutation,
  useUpdateDatastoreConnectionSecretsMutation,
} from "datastore-connections/datastore-connection.slice";
import {
  CreateSaasConnectionConfigRequest,
  CreateSaasConnectionConfigResponse,
  DatastoreConnectionSecretsRequest,
  DatastoreConnectionSecretsResponse,
} from "datastore-connections/types";
import { useState } from "react";

import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import { usePatchSystemConnectionConfigsMutation } from "~/features/system/system.slice";
import {
  AccessLevel,
  BulkPutConnectionConfiguration,
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  ConnectionType,
  SystemType,
} from "~/types/api";

import { ConnectionConfigFormValues } from "../types";
import ConnectorParametersForm from "./ConnectorParametersForm";
import { useGetConnectionTypeSecretSchemaQuery } from "~/features/connection-type";
import TestConnection from "datastore-connections/add-connection/TestConnection";

/**
 * Only handles creating saas connectors. The BE handler automatically
 * configures the connector using the saas config and creates the
 * `DatasetConfig` and `Dataset`.
 */
const createSaasConnector = async (
  values: ConnectionConfigFormValues,
  secretsSchema: ConnectionTypeSecretSchemaReponse,
  connectionOption: ConnectionSystemTypeMap,
  systemFidesKey: string,
  createSaasConnectorFunc: any
) => {
  const connectionConfig: CreateSaasConnectionConfigRequest = {
    description: values.description,
    name: values.name,
    instance_key: formatKey(values.instance_key as string),
    saas_connector_type: connectionOption.identifier,
    secrets: {},
  };

  const params: CreateSaasConnectionConfig = {
    systemFidesKey,
    connectionConfig,
  };

  Object.entries(secretsSchema!.properties).forEach((key) => {
    params.connectionConfig.secrets[key[0]] = values[key[0]];
  });
  console.log("about to create a new saas connector", params);
  return (await createSaasConnectorFunc(
    params
  ).unwrap()) as CreateSaasConnectionConfigResponse;
};

/**
 * Database connectors: creating and patching
 *
 * Saas connectors: patching
 */
const patchConnectionConfig = async (
  values: ConnectionConfigFormValues,
  secretsSchema: ConnectionTypeSecretSchemaReponse,
  connectionOption: ConnectionSystemTypeMap,
  systemFidesKey: string,
  connectionConfig: ConnectionConfigurationResponse,
  patchFunc: any
) => {
  console.log(
    "connection_type: ",
    values,
    " connectionOptionId: ",
    connectionOption?.identifier
  );


  const key =
    [SystemType.DATABASE, SystemType.EMAIL].indexOf(connectionOption.type) > -1
      ? formatKey(values.instance_key as string)
      : connectionConfig?.key;

  const params1: Omit<ConnectionConfigurationResponse, "created_at"> = {
    access: AccessLevel.WRITE,
    connection_type: (connectionOption.type === SystemType.SAAS
      ? connectionOption.type
      : connectionOption.identifier) as ConnectionType,
    description: values.description,
    disabled: false,
    key,
    name: values.name,
  };
  const payload = await patchFunc({
    systemFidesKey,
    connectionConfigs: [params1],
  }).unwrap();

  if (payload.failed?.length > 0) {
    const error = payload.failed[0].message as string;
    throw Object.assign(Error(error), {
      data: {
        detail: error,
      },
    });
  }
  return payload as BulkPutConnectionConfiguration;
};

const upsertConnectionConfigSecrets = async (
  values: ConnectionConfigFormValues,
  secretsSchema: ConnectionTypeSecretSchemaReponse,
  connectionConfigFidesKey: string,
  upsertFunc: any
) => {
  const params2: DatastoreConnectionSecretsRequest = {
    connection_key: connectionConfigFidesKey,
    secrets: {},
  };
  Object.entries(secretsSchema!.properties).forEach((key) => {
    params2.secrets[key[0]] = values[key[0]];
  });

  return (await upsertFunc(
    params2
  ).unwrap()) as DatastoreConnectionSecretsResponse;
};

type ConnectorParametersProps = {
  systemFidesKey: string;
  connectionOption: ConnectionSystemTypeMap;
  connectionConfig?: ConnectionConfigurationResponse;
};

export const useConnectorForm = ({
  secretsSchema,
  systemFidesKey,
  connectionOption,
  connectionConfig,
}: Pick<
  ConnectorParametersProps,
  "systemFidesKey" | "connectionOption" | "connectionConfig"
> & {
  secretsSchema?: ConnectionTypeSecretSchemaReponse;
}) => {
  const { errorAlert, successAlert } = useAlert();
  const { handleError } = useAPIHelper();

  const [isSubmitting, setIsSubmitting] = useState(false);

  const [createSassConnectionConfig] = useCreateSassConnectionConfigMutation();
  const [updateDatastoreConnectionSecrets] =
    useUpdateDatastoreConnectionSecretsMutation();
  const [patchDatastoreConnection] = usePatchSystemConnectionConfigsMutation();

  const handleSubmit = async (values: ConnectionConfigFormValues) => {
    try {
      setIsSubmitting(true);
      console.log("submitting: ", connectionOption.type, connectionConfig);
      if (
        connectionOption.type === SystemType.SAAS &&
        connectionConfig === undefined
      ) {
        const response = await createSaasConnector(
          values,
          secretsSchema!,
          connectionOption,
          systemFidesKey,
          createSassConnectionConfig
        );
        connectionConfig = response.connection;
        successAlert(`Connector successfully added!`);
      } else {
        const payload = await patchConnectionConfig(
          values,
          secretsSchema!,
          connectionOption,
          systemFidesKey,
          connectionConfig!,
          patchDatastoreConnection
        );
        const payload2 = await upsertConnectionConfigSecrets(
          values,
          secretsSchema!,
          payload.succeeded[0].key,
          updateDatastoreConnectionSecrets
        );
      }
      console.log(values);
      //TODO: Add patching of DatasetConfig here.
      // it requires a connectionConfig so it must come after the submission
      // if creating a brand new connection there would be no connectionConfig
      // to link it to

      // I think it's worth moving the testing phase to the very end
      // I need to make sure the semantics around that are good

      // if (payload2.test_status === "failed") {
      //   errorAlert(
      //     <>
      //       <b>Message:</b> {payload2.msg}
      //       <br />
      //       <b>Failure Reason:</b> {payload2.failure_reason}
      //     </>
      //   );
      // } else {
      //   successAlert(
      //     `Connector successfully ${
      //       connectionConfig?.key ? "updated" : "added"
      //     }!`
      //   );
      // }
    } catch (error) {
      handleError(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return { isSubmitting, handleSubmit };
};

export const ConnectorParameters: React.FC<ConnectorParametersProps> = ({
  systemFidesKey,
  connectionOption,
  connectionConfig,
}) => {
  const defaultValues: ConnectionConfigFormValues = {
    description: "",
    instance_key: "",
    name: "",
  };

  const [response, setResponse] = useState<any>();

  const handleTestConnectionClick = (value: any) => {
    setResponse(value);
  };
  const skip = connectionOption.type === SystemType.MANUAL;
  const { data: secretsSchema } = useGetConnectionTypeSecretSchemaQuery(
    connectionOption!.identifier,
    {
      skip,
    }
  );

  const { isSubmitting, handleSubmit } = useConnectorForm({
    secretsSchema,
    systemFidesKey,
    connectionOption,
    connectionConfig,
  });
  if (!secretsSchema) {
    return null;
  }

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
        onTestConnectionClick={handleTestConnectionClick}
        connectionOption={connectionOption}
        connection={connectionConfig}
      />

      {response && (
        <SlideFade in>
          <Box mt="16px" maxW="528px" w="fit-content">
            <TestConnection response={response} />
          </Box>
        </SlideFade>
      )}
    </>
  );
};
