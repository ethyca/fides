import { useAPIHelper } from "common/hooks";
import { useAlert } from "common/hooks/useAlert";
import { ConnectionTypeSecretSchemaResponse } from "connection-type/types";
import {
  CreateSaasConnectionConfig,
  useCreateSassConnectionConfigMutation,
  useLazyGetAuthorizationUrlQuery,
} from "datastore-connections/datastore-connection.slice";
import {
  CreateSaasConnectionConfigRequest,
  CreateSaasConnectionConfigResponse,
  DatastoreConnectionSecretsResponse,
} from "datastore-connections/types";
import { Box, Flex, Spacer, useToast, UseToastOptions } from "fidesui";
import { useMemo, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import DocsLink from "~/features/common/DocsLink";
import { useFeatures } from "~/features/common/features";
import RightArrow from "~/features/common/Icon/RightArrow";
import { DEFAULT_TOAST_PARAMS } from "~/features/common/toast";
import { useGetConnectionTypeSecretSchemaQuery } from "~/features/connection-type";
import { useDatasetConfigField } from "~/features/datastore-connections/system_portal_config/forms/fields/DatasetConfigField/useDatasetConfigField";
import TestConnectionMessage from "~/features/datastore-connections/system_portal_config/TestConnectionMessage";
import { TestData } from "~/features/datastore-connections/TestData";
import {
  useCreatePlusSaasConnectionConfigMutation,
  usePatchPlusSystemConnectionConfigsMutation,
} from "~/features/plus/plus.slice";
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
  ActionType,
  BulkPutConnectionConfiguration,
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  ConnectionType,
  SystemResponse,
  SystemType,
} from "~/types/api";

import { ConnectionConfigFormValues } from "../types";
import {
  ConnectorParametersForm,
  TestConnectionResponse,
} from "./ConnectorParametersForm";
import { generateIntegrationKey } from "./helpers";

/**
 * Only handles creating saas connectors. The BE handler automatically
 * configures the connector using the saas config and creates the
 * `DatasetConfig` and `Dataset`.
 */
const createSaasConnector = async (
  values: ConnectionConfigFormValues,
  secretsSchema: ConnectionTypeSecretSchemaResponse,
  connectionOption: ConnectionSystemTypeMap,
  systemFidesKey: string,
  createSaasConnectorFunc: any,
) => {
  const connectionConfig: Omit<CreateSaasConnectionConfigRequest, "name"> = {
    description: values.description || "",
    instance_key: generateIntegrationKey(systemFidesKey, connectionOption),
    saas_connector_type: connectionOption.identifier,
    secrets: {},
    ...(values.enabled_actions
      ? { enabled_actions: values.enabled_actions }
      : {}),
  };

  const params: CreateSaasConnectionConfig = {
    systemFidesKey,
    connectionConfig,
  };

  Object.entries(secretsSchema!.properties).forEach((key) => {
    params.connectionConfig.secrets[key[0]] = values.secrets[key[0]];
  });
  return (await createSaasConnectorFunc(
    params,
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
  patchFunc: any,
) => {
  const key = connectionConfig
    ? connectionConfig.key
    : generateIntegrationKey(systemFidesKey, connectionOption);

  // the enabled_actions are conditionally added if plus is enabled
  const params1: Omit<ConnectionConfigurationResponse, "created_at" | "name"> =
    {
      access: AccessLevel.WRITE,
      connection_type: (connectionOption.type === SystemType.SAAS
        ? connectionOption.type
        : connectionOption.identifier) as ConnectionType,
      description: values.description,
      disabled: false,
      key,
      ...(values.enabled_actions
        ? { enabled_actions: values.enabled_actions as ActionType[] }
        : {}),
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
  secretsSchema: ConnectionTypeSecretSchemaResponse,
  systemFidesKey: string,
  originalSecrets: Record<string, string>,
  patchFunc: any,
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
    params2,
  ).unwrap()) as DatastoreConnectionSecretsResponse;
};

type ConnectorParametersProps = {
  systemFidesKey: string;
  connectionOption: ConnectionSystemTypeMap;
  setSelectedConnectionOption: (
    option: ConnectionSystemTypeMap | undefined,
  ) => void;
  connectionConfig?: ConnectionConfigurationResponse | null;
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
  secretsSchema?: ConnectionTypeSecretSchemaResponse;
}) => {
  const { successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const dispatch = useAppDispatch();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAuthorizing, setIsAuthorizing] = useState(false);

  const {
    dropdownOptions: datasetDropdownOptions,
    patchConnectionDatasetConfig,
    initialDatasets,
  } = useDatasetConfigField({
    connectionConfig,
  });

  const [createSassConnectionConfig] = useCreateSassConnectionConfigMutation();
  const [createPlusSaasConnectionConfig] =
    useCreatePlusSaasConnectionConfigMutation();
  const [getAuthorizationUrl] = useLazyGetAuthorizationUrlQuery();
  const [updateSystemConnectionSecrets] =
    usePatchSystemConnectionSecretsMutation();
  const [patchDatastoreConnection] = usePatchSystemConnectionConfigsMutation();
  const [patchPlusDatastoreConnection] =
    usePatchPlusSystemConnectionConfigsMutation();
  const [deleteDatastoreConnection, deleteDatastoreConnectionResult] =
    useDeleteSystemConnectionConfigMutation();
  const { plus: isPlusEnabled } = useFeatures();

  const originalSecrets = useMemo(
    () => connectionConfig?.secrets ?? {},
    [connectionConfig],
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
          isPlusEnabled
            ? createPlusSaasConnectionConfig
            : createSassConnectionConfig,
        );
        // eslint-disable-next-line no-param-reassign
        connectionConfig = response.connection;
      } else {
        const payload = await patchConnectionConfig(
          values,
          connectionOption,
          systemFidesKey,
          connectionConfig!,
          isPlusEnabled
            ? patchPlusDatastoreConnection
            : patchDatastoreConnection,
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
            updateSystemConnectionSecrets,
          );
        }
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
        }!`,
      );
    } catch (error) {
      handleError(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAuthorization = async (values: ConnectionConfigFormValues) => {
    const isCreatingConnectionConfig = !connectionConfig;
    try {
      setIsAuthorizing(true);
      if (isCreatingConnectionConfig) {
        const response = await createSaasConnector(
          values, // pre-process dataset references
          secretsSchema!,
          connectionOption,
          systemFidesKey,
          createSassConnectionConfig,
        );
        // eslint-disable-next-line no-param-reassign
        connectionConfig = response.connection;
      } else {
        await upsertConnectionConfigSecrets(
          values,
          secretsSchema!,
          systemFidesKey,
          originalSecrets,
          updateSystemConnectionSecrets,
        );
      }
      const authorizationUrl = (await getAuthorizationUrl(
        connectionConfig!.key,
      ).unwrap()) as string;

      setIsAuthorizing(false);

      // workaround to make sure isAuthorizing is set to false before redirecting
      setTimeout(() => {
        window.location.href = authorizationUrl;
      }, 0);
    } catch (error) {
      handleError(error);
    } finally {
      setIsAuthorizing(false);
    }
  };

  return {
    isSubmitting,
    isAuthorizing,
    handleSubmit,
    handleAuthorization,
    datasetDropdownOptions,
    initialDatasets,
    handleDelete,
    deleteDatastoreConnectionResult,
  };
};

export const ConnectorParameters = ({
  systemFidesKey,
  connectionOption,
  connectionConfig,
  setSelectedConnectionOption,
}: ConnectorParametersProps) => {
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
    },
  );

  const {
    isSubmitting,
    isAuthorizing,
    handleSubmit,
    handleAuthorization,
    datasetDropdownOptions,
    initialDatasets,
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
    dataset: [],
  };

  if (!secretsSchema && connectionOption.type !== SystemType.MANUAL) {
    return null;
  }

  return (
    <>
      <Box
        borderRadius="6px"
        border="1px"
        borderColor="gray.200"
        backgroundColor="gray.50"
        fontSize="14px"
        p={4}
        mb={4}
      >
        <div>
          Connect to your {connectionOption!.human_readable} environment by
          providing the information below. Once you have saved the form, you may
          test the integration to confirm that it&apos;s working correctly.
        </div>
        {connectionOption.user_guide && (
          <div style={{ marginTop: "12px" }}>
            <DocsLink href={connectionOption.user_guide}>
              View docs for help with this integration <RightArrow />
            </DocsLink>
          </div>
        )}
      </Box>
      <ConnectorParametersForm
        secretsSchema={secretsSchema}
        defaultValues={defaultValues}
        isSubmitting={isSubmitting}
        isAuthorizing={isAuthorizing}
        onSaveClick={handleSubmit}
        onTestConnectionClick={handleTestConnectionClick}
        onAuthorizeConnectionClick={handleAuthorization}
        connectionOption={connectionOption}
        connectionConfig={connectionConfig}
        datasetDropdownOptions={datasetDropdownOptions}
        initialDatasets={initialDatasets}
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
