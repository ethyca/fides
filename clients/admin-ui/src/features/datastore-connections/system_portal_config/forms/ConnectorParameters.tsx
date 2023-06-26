import { Box, Flex, SlideFade, Spacer } from "@fidesui/react";
import { useAPIHelper } from "common/hooks";
import { useAlert } from "common/hooks/useAlert";
import { ConnectionTypeSecretSchemaReponse } from "connection-type/types";
import {
  CreateSaasConnectionConfig,
  useCreateSassConnectionConfigMutation,
  useDeleteDatastoreConnectionMutation,
  useGetConnectionConfigDatasetConfigsQuery,
  useUpdateDatastoreConnectionSecretsMutation,
} from "datastore-connections/datastore-connection.slice";
import { useDatasetConfigField } from "datastore-connections/system_portal_config/forms/fields/DatasetConfigField/DatasetConfigField";
import {
  CreateSaasConnectionConfigRequest,
  CreateSaasConnectionConfigResponse,
  DatastoreConnectionSecretsRequest,
  DatastoreConnectionSecretsResponse,
} from "datastore-connections/types";
import { useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { useGetConnectionTypeSecretSchemaQuery } from "~/features/connection-type";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import TestConnection from "~/features/datastore-connections/system_portal_config/TestConnection";
import TestData from "~/features/datastore-connections/TestData";
import {
  selectActiveSystem,
  setActiveSystem,
  usePatchSystemConnectionConfigsMutation,
} from "~/features/system/system.slice";
import {
  AccessLevel,
  BulkPutConnectionConfiguration,
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  ConnectionType,
  SystemResponse,
  SystemType,
} from "~/types/api";

import { ConnectionConfigFormValues } from "../types";
import ConnectorParametersForm from "./ConnectorParametersForm";

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
  return (await createSaasConnectorFunc(
    params
  ).unwrap()) as CreateSaasConnectionConfigResponse;
};

/**
 * Database connectors: creating and patching
 *
 * Saas connectors: patching
 */
export const patchConnectionConfig = async (
  values: ConnectionConfigFormValues,
  connectionOption: ConnectionSystemTypeMap,
  systemFidesKey: string,
  connectionConfig: ConnectionConfigurationResponse,
  patchFunc: any
) => {
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
  setSelectedConnectionOption: (
    option: ConnectionSystemTypeMap | undefined
  ) => void;
  connectionConfig?: ConnectionConfigurationResponse;
};

export const useConnectorForm = ({
  secretsSchema,
  systemFidesKey,
  connectionOption,
  connectionConfig,
  setSelectedConnectionOption,
}: Pick<
  ConnectorParametersProps,
  | "systemFidesKey"
  | "connectionOption"
  | "connectionConfig"
  | "setSelectedConnectionOption"
> & {
  secretsSchema?: ConnectionTypeSecretSchemaReponse;
}) => {
  const { successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const dispatch = useAppDispatch();

  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    dropdownOptions: datasetDropdownOptions,
    upsertDataset,
    patchConnectionDatasetConfig,
    datasetConfigFidesKey: selectedDatasetConfigOption,
  } = useDatasetConfigField({
    connectionConfig,
  });

  const [createSassConnectionConfig] = useCreateSassConnectionConfigMutation();
  const [updateDatastoreConnectionSecrets] =
    useUpdateDatastoreConnectionSecretsMutation();
  const [patchDatastoreConnection] = usePatchSystemConnectionConfigsMutation();
  const [deleteDatastoreConnection, deleteDatastoreConnectionResult] =
    useDeleteDatastoreConnectionMutation();
  const { data: allDatasetConfigs } = useGetConnectionConfigDatasetConfigsQuery(
    connectionConfig?.key || ""
  );

  const activeSystem = useAppSelector(selectActiveSystem) as SystemResponse;

  const handleDelete = async (id: string) => {
    try {
      await deleteDatastoreConnection(id);
      // @ts-ignore connection_configs isn't on the type yet but will be in the future
      dispatch(setActiveSystem({ ...activeSystem, connection_configs: null }));
      setSelectedConnectionOption(undefined);
      successAlert(`Integration successfully deleted!`);
    } catch (e) {
      handleError(e);
    }
  };

  const handleSubmit = async (values: ConnectionConfigFormValues) => {
    const isCreatingConnectionConfig = !connectionConfig;
    const hasLinkedDatasetConfig = allDatasetConfigs
      ? allDatasetConfigs.items.length > 0
      : false;
    try {
      setIsSubmitting(true);
      if (
        connectionOption.type === SystemType.SAAS &&
        isCreatingConnectionConfig
      ) {
        const response = await createSaasConnector(
          values,
          secretsSchema!,
          connectionOption,
          systemFidesKey,
          createSassConnectionConfig
        );
        // eslint-disable-next-line no-param-reassign
        connectionConfig = response.connection;
      } else {
        const payload = await patchConnectionConfig(
          values,
          connectionOption,
          systemFidesKey,
          connectionConfig!,
          patchDatastoreConnection
        );
        if (
          !connectionConfig &&
          connectionOption.type === SystemType.DATABASE
        ) {
          /*
          The connectionConfig is required for patching the datasetConfig
           */
          // eslint-disable-next-line prefer-destructuring,no-param-reassign
          connectionConfig = payload.succeeded[0];
        }

        if (connectionOption.type !== SystemType.MANUAL) {
          const secretsPayload = values;

          await upsertConnectionConfigSecrets(
            secretsPayload,
            secretsSchema!,
            payload.succeeded[0].key,
            updateDatastoreConnectionSecrets
          );
        }
      }

      if (
        values.datasetYaml &&
        !values.dataset &&
        connectionOption.type === SystemType.DATABASE &&
        !hasLinkedDatasetConfig
      ) {
        const res = await upsertDataset(values.datasetYaml);
        // eslint-disable-next-line no-param-reassign
        values.dataset = res;
      }

      if (
        connectionConfig &&
        values.dataset &&
        connectionOption.type === SystemType.DATABASE
      ) {
        await patchConnectionDatasetConfig(values, connectionConfig.key);
      }

      successAlert(
        `Integration successfully ${
          isCreatingConnectionConfig ? "added" : "updated"
        }!`
      );
    } catch (error) {
      handleError(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    isSubmitting,
    handleSubmit,
    datasetDropdownOptions,
    selectedDatasetConfigOption,
    handleDelete,
    deleteDatastoreConnectionResult,
  };
};

export const ConnectorParameters: React.FC<ConnectorParametersProps> = ({
  systemFidesKey,
  connectionOption,
  connectionConfig,
  setSelectedConnectionOption,
}) => {
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

  const {
    isSubmitting,
    handleSubmit,
    datasetDropdownOptions,
    selectedDatasetConfigOption,
    handleDelete,
    deleteDatastoreConnectionResult,
  } = useConnectorForm({
    secretsSchema,
    systemFidesKey,
    connectionOption,
    connectionConfig,
    setSelectedConnectionOption,
  });

  const defaultValues: ConnectionConfigFormValues = {
    description: "",
    instance_key: "",
    name: "",
    dataset: selectedDatasetConfigOption,
    datasetYaml: undefined,
  };

  if (!secretsSchema && connectionOption.type !== SystemType.MANUAL) {
    return null;
  }

  return (
    <>
      <Box color="gray.700" fontSize="14px" mb={4} h="80px">
        Connect to your {connectionOption!.human_readable} environment by
        providing credential information below. Once you have saved your
        integration credentials, you can review what data is included when
        processing a privacy request in your Dataset configuration.
      </Box>
      <ConnectorParametersForm
        secretsSchema={secretsSchema}
        defaultValues={defaultValues}
        isSubmitting={isSubmitting}
        onSaveClick={handleSubmit}
        onTestConnectionClick={handleTestConnectionClick}
        connectionOption={connectionOption}
        connectionConfig={connectionConfig}
        datasetDropdownOptions={datasetDropdownOptions}
        isCreatingConnectionConfig={!connectionConfig}
        onDelete={handleDelete}
        deleteResult={deleteDatastoreConnectionResult}
      />

      {connectionConfig ? (
        <Flex mt="4" justifyContent="between" alignItems="center">
          {response ? (
            <TestData
              succeeded={response.data.test_status === "succeeded"}
              timestamp={response.fulfilledTimeStamp}
            />
          ) : (
            <TestData
              succeeded={connectionConfig?.last_test_succeeded}
              timestamp={connectionConfig?.last_test_timestamp || ""}
            />
          )}
          <Spacer />
        </Flex>
      ) : null}

      {response && (
        <SlideFade in>
          <Box mt="16px" maxW="528px" w="fit-content">
            <TestConnection
              response={response}
              connectionOption={connectionOption}
            />
          </Box>
        </SlideFade>
      )}
    </>
  );
};
