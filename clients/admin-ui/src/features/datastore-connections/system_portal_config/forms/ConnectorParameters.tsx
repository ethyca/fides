import { Box, Flex, Spacer, useToast, UseToastOptions } from "@fidesui/react";
import { useAPIHelper } from "common/hooks";
import { useAlert } from "common/hooks/useAlert";
import { ConnectionTypeSecretSchemaReponse } from "connection-type/types";
import {
  CreateSaasConnectionConfig,
  useCreateSassConnectionConfigMutation,
  useGetConnectionConfigDatasetConfigsQuery,
} from "datastore-connections/datastore-connection.slice";
import { useDatasetConfigField } from "datastore-connections/system_portal_config/forms/fields/DatasetConfigField/DatasetConfigField";
import {
  CreateSaasConnectionConfigRequest,
  CreateSaasConnectionConfigResponse,
  DatastoreConnectionSecretsResponse,
} from "datastore-connections/types";
import { useMemo, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { DEFAULT_TOAST_PARAMS } from "~/features/common/toast";
import { useGetConnectionTypeSecretSchemaQuery } from "~/features/connection-type";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import TestConnectionMessage from "~/features/datastore-connections/system_portal_config/TestConnectionMessage";
import TestData from "~/features/datastore-connections/TestData";
import {
  ConnectionConfigSecretsRequest,
  selectActiveSystem,
  setActiveSystem,
  useDeleteSystemConnectionConfigMutation,
  usePatchSystemConnectionConfigsMutation,
  usePatchSystemConnectionSecretsMutation,
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
import ConnectorParametersForm, {
  TestConnectionResponse,
} from "./ConnectorParametersForm";

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
  const connectionConfig: Omit<CreateSaasConnectionConfigRequest, "name"> = {
    description: values.description,
    instance_key: formatKey(values.instance_key as string),
    saas_connector_type: connectionOption.identifier,
    secrets: {},
  };

  const params: CreateSaasConnectionConfig = {
    systemFidesKey,
    connectionConfig,
  };

  Object.entries(secretsSchema!.properties).forEach((key) => {
    params.connectionConfig.secrets[key[0]] = values.secrets[key[0]];
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
    [SystemType.DATABASE, SystemType.EMAIL, SystemType.MANUAL].indexOf(
      connectionOption.type
    ) > -1
      ? formatKey(values.instance_key as string)
      : connectionConfig?.key;

  const params1: Omit<ConnectionConfigurationResponse, "created_at" | "name"> =
    {
      access: AccessLevel.WRITE,
      connection_type: (connectionOption.type === SystemType.SAAS
        ? connectionOption.type
        : connectionOption.identifier) as ConnectionType,
      description: values.description,
      disabled: false,
      key,
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
  systemFidesKey: string,
  originalSecrets: Record<string, string>,
  patchFunc: any
) => {
  const params2: ConnectionConfigSecretsRequest = {
    systemFidesKey,
    secrets: {},
  };
  Object.entries(secretsSchema!.properties).forEach((key) => {
    /*
     * Only patch secrets that have changed. Otherwise, sensitive secrets
     * would get overwritten with "**********" strings
     */
    if (
      !(key[0] in originalSecrets) ||
      values.secrets[key[0]] !== originalSecrets[key[0]]
    ) {
      params2.secrets[key[0]] = values.secrets[key[0]];
    }
  });

  if (Object.keys(params2.secrets).length === 0) {
    return Promise.resolve();
  }

  return (await patchFunc(
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
  const [updateSystemConnectionSecrets] =
    usePatchSystemConnectionSecretsMutation();
  const [patchDatastoreConnection] = usePatchSystemConnectionConfigsMutation();
  const [deleteDatastoreConnection, deleteDatastoreConnectionResult] =
    useDeleteSystemConnectionConfigMutation();
  const { data: allDatasetConfigs } = useGetConnectionConfigDatasetConfigsQuery(
    connectionConfig?.key || ""
  );

  const originalSecrets = useMemo(
    () => (connectionConfig ? { ...connectionConfig.secrets } : {}),
    [connectionConfig]
  );
  const activeSystem = useAppSelector(selectActiveSystem) as SystemResponse;

  const handleDelete = async () => {
    try {
      await deleteDatastoreConnection(systemFidesKey);
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
            systemFidesKey,
            originalSecrets,
            updateSystemConnectionSecrets
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
  const [response, setResponse] = useState<TestConnectionResponse>();

  const toast = useToast();

  const handleTestConnectionClick = (value: TestConnectionResponse) => {
    setResponse(value);
    const status: UseToastOptions["status"] =
      value.data?.test_status === "succeeded" ? "success" : "error";
    const toastParams = {
      ...DEFAULT_TOAST_PARAMS,
      status,
      description: <TestConnectionMessage status={status} />,
    };
    toast(toastParams);
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
          {response &&
          response.data &&
          response.fulfilledTimeStamp !== undefined ? (
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
    </>
  );
};
