import {
  Card,
  Flex,
  Form,
  Input,
  Select,
  Spin,
  Text,
  useMessage,
} from "fidesui";
import { isEmpty, isUndefined, mapValues, omitBy } from "lodash";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useFeatures } from "~/features/common/features";
import { FormFieldFromSchema } from "~/features/common/form/FormFieldFromSchema";
import { useFormFieldsFromSchema } from "~/features/common/form/useFormFieldsFromSchema";
import { getErrorMessage } from "~/features/common/helpers";
import { INTEGRATION_DETAIL_ROUTE } from "~/features/common/nav/routes";
import { debounce } from "~/features/common/utils";
import { useGetConnectionTypeSecretSchemaQuery } from "~/features/connection-type";
import type { ConnectionTypeSecretSchemaResponse } from "~/features/connection-type/types";
import { useGetAllFilteredDatasetsQuery } from "~/features/dataset";
import {
  useCreateUnlinkedSassConnectionConfigMutation,
  usePatchDatastoreConnectionMutation,
  usePatchDatastoreConnectionSecretsMutation,
} from "~/features/datastore-connections";
import { useDatasetConfigField } from "~/features/datastore-connections/system_portal_config/forms/fields/DatasetConfigField/useDatasetConfigField";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import { useSetSystemLinksMutation } from "~/features/integrations/system-links.slice";
import { useIntegrationPropertySelect } from "~/features/properties/useIntegrationPropertySelect";
import {
  useGetSystemsQuery,
  usePatchSystemConnectionConfigsMutation,
} from "~/features/system";
import {
  AccessLevel,
  BigQueryDocsSchema,
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  ConnectionType,
  DynamoDBDocsSchema,
  ScyllaDocsSchema,
  SystemType,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

type ConnectionSecrets = Partial<
  BigQueryDocsSchema & ScyllaDocsSchema & DynamoDBDocsSchema
>;

type FormValues = {
  name: string;
  description: string;
  system_fides_key?: string;
  secrets?: ConnectionSecrets;
  dataset?: string[];
  property_ids?: string[];
};

const PROPERTY_UPDATE_FAILED_MSG =
  "Integration saved but failed to update properties. Please try again";

export const ConfigureIntegrationForm = ({
  connection,
  connectionOption,
  onClose,
  description,
  onFormStateChange,
  initialSystemFidesKey,
}: {
  connection?: ConnectionConfigurationResponse;
  connectionOption: ConnectionSystemTypeMap;
  onClose: () => void;
  description: React.ReactNode;
  onFormStateChange?: (formState: {
    dirty: boolean;
    isValid: boolean;
    submitForm: () => void;
    loading: boolean;
  }) => void;
  initialSystemFidesKey?: string;
}) => {
  const [
    patchConnectionSecretsMutationTrigger,
    { isLoading: secretsIsLoading },
  ] = usePatchDatastoreConnectionSecretsMutation();
  const [patchDatastoreConnectionsTrigger, { isLoading: patchIsLoading }] =
    usePatchDatastoreConnectionMutation();
  const [patchSystemConnectionsTrigger, { isLoading: systemPatchIsLoading }] =
    usePatchSystemConnectionConfigsMutation();
  const router = useRouter();

  const [createUnlinkedSassConnectionConfigTrigger] =
    useCreateUnlinkedSassConnectionConfigMutation();

  const [setSystemLinks] = useSetSystemLinksMutation();

  const { plus: hasPlus } = useFeatures();

  const isEditing = !!connection;

  const {
    propertyOptions,
    initialPropertyIds,
    savePropertyAssignments,
    hasDatasets,
    isLoading: isLoadingProperties,
  } = useIntegrationPropertySelect(connection?.key);

  const hasSecrets =
    connectionOption.identifier !== ConnectionType.MANUAL_TASK &&
    connectionOption.identifier !== ConnectionType.JIRA_TICKET;

  const { data: secrets, isLoading: secretsSchemaIsLoading } =
    useGetConnectionTypeSecretSchemaQuery(connectionOption.identifier, {
      skip: !hasSecrets,
    });

  // System select search state
  const [systemSearchValue, setSystemSearchValue] = useState<string>();
  const OPTIONS_LIMIT = 25;

  // Fetch systems for the select dropdown
  const { data: systemsData, isFetching: isFetchingSystems } =
    useGetSystemsQuery({
      page: 1,
      size: OPTIONS_LIMIT,
      search: systemSearchValue || undefined,
    });

  const systemOptions = useMemo(
    () =>
      systemsData?.items?.map((system) => ({
        value: system.fides_key,
        label: system.name,
      })) || [],
    [systemsData],
  );

  // Handle system search with debouncing
  const handleSystemSearch = useCallback(
    (search: string) => {
      if (search?.length > 1) {
        setSystemSearchValue(search);
      }
      if (search?.length === 0) {
        setSystemSearchValue(undefined);
      }
    },
    [setSystemSearchValue],
  );

  const onSystemSearch = useMemo(
    () => debounce(handleSystemSearch, 300),
    [handleSystemSearch],
  );

  const { data: allDatasets } = useGetAllFilteredDatasetsQuery({
    minimal: true,
    connection_type: ConnectionType.BIGQUERY,
  });
  const datasetOptions = allDatasets?.map((d) => ({
    label: d.name ?? d.fides_key,
    value: d.fides_key,
  }));

  const { patchConnectionDatasetConfig, initialDatasets } =
    useDatasetConfigField({
      connectionConfig: connection,
    });

  const { getFieldValidation, preprocessValues } =
    useFormFieldsFromSchema(secrets);

  const initialValues: FormValues = useMemo(
    () => ({
      name: connection?.name ?? "",
      description: connection?.description ?? "",
      system_fides_key: initialSystemFidesKey,
      ...(hasSecrets && {
        secrets: mapValues(secrets?.properties, (s, key) => {
          const value = connection?.secrets?.[key] ?? s.default;
          // Convert booleans to strings to match select options
          if (typeof value === "boolean") {
            return String(value);
          }
          return value ?? "";
        }),
      }),
      dataset: initialDatasets,
      property_ids: initialPropertyIds,
    }),
    [
      connection,
      initialSystemFidesKey,
      hasSecrets,
      secrets,
      initialDatasets,
      initialPropertyIds,
    ],
  );

  const [form] = Form.useForm<FormValues>();

  const messageApi = useMessage();

  const isSaas = connectionOption.type === SystemType.SAAS;

  // Exclude secrets fields that haven't changed
  // The api returns secrets masked as asterisks (*****)
  // and we don't want to PATCH with those values.
  const excludeUnchangedSecrets = (secretsValues: ConnectionSecrets) =>
    omitBy(
      mapValues(secretsValues, (s, key) => {
        const original = connection?.secrets?.[key] ?? "";
        // Convert both to strings for comparison to handle booleans and numbers
        return String(original) === String(s) ? undefined : s;
      }),
      isUndefined,
    );

  const handlePropertySave = async (propertyIds: string[]) => {
    try {
      await savePropertyAssignments(propertyIds);
    } catch {
      messageApi.error(PROPERTY_UPDATE_FAILED_MSG);
    }
  };

  const handleSubmit = async (values: FormValues) => {
    const processedValues = preprocessValues(values);

    const newSecretsValues = hasSecrets
      ? excludeUnchangedSecrets(processedValues.secrets!)
      : {};

    const connectionPayload = isEditing
      ? {
          ...connection,
          disabled: connection.disabled ?? false,
          name: values.name,
          description: values.description,
          secrets: undefined,
        }
      : {
          name: values.name,
          key: formatKey(values.name),
          connection_type: (isSaas
            ? ConnectionType.SAAS
            : connectionOption.identifier) as ConnectionType,
          access: AccessLevel.READ,
          disabled: false,
          description: values.description,
          secrets: processedValues.secrets,
          dataset: values.dataset,
          ...(isSaas
            ? { saas_connector_type: connectionOption.identifier }
            : {}),
        };

    // if system is attached, use patch request that attaches to system
    let patchResult;
    if (values.system_fides_key) {
      patchResult = await patchSystemConnectionsTrigger({
        systemFidesKey: values.system_fides_key,
        connectionConfigs: [connectionPayload],
      });
    } else if (isSaas && !isEditing) {
      patchResult = await createUnlinkedSassConnectionConfigTrigger({
        ...connectionPayload,
        instance_key: formatKey(values.name),
        saas_connector_type: connectionOption.identifier,
        secrets: values.secrets || {},
      });
    } else {
      patchResult = await patchDatastoreConnectionsTrigger(connectionPayload);
    }
    if (isErrorResult(patchResult)) {
      const patchErrorMsg = getErrorMessage(
        patchResult.error,
        `A problem occurred while ${
          isEditing ? "updating" : "creating"
        } this integration. Please try again.`,
      );
      messageApi.error(patchErrorMsg);
      return;
    }
    if (!hasSecrets || !values.secrets) {
      // Link system if provided (using system-links API)
      if (values.system_fides_key && connectionPayload.key) {
        try {
          await setSystemLinks({
            connectionKey: connectionPayload.key,
            body: {
              links: [
                {
                  system_fides_key: values.system_fides_key,
                },
              ],
            },
          }).unwrap();
        } catch (error) {
          messageApi.error(
            "Integration saved but system linking failed. You can link it later.",
          );
        }
      }

      // Save property assignments if editing
      if (isEditing && values.property_ids !== undefined && hasDatasets) {
        await handlePropertySave(values.property_ids);
      }

      messageApi.success(
        `Integration ${isEditing ? "updated" : "created"} successfully`,
      );

      onClose();

      // Redirect to the newly created integration detail page
      if (!isEditing) {
        router.push({
          pathname: INTEGRATION_DETAIL_ROUTE,
          query: {
            id: connectionPayload.key,
          },
        });
      }

      if (
        connectionPayload &&
        values.dataset &&
        connectionOption.identifier === ConnectionType.DATAHUB
      ) {
        await patchConnectionDatasetConfig(values, connectionPayload.key, {
          showSuccessAlert: false,
        });
      }
      return;
    }

    // if provided, update secrets with separate request
    if (!isEmpty(newSecretsValues)) {
      const secretsResult = await patchConnectionSecretsMutationTrigger({
        connection_key: connectionPayload.key,
        secrets: newSecretsValues,
      });

      if (isErrorResult(secretsResult)) {
        const secretsErrorMsg = getErrorMessage(
          secretsResult.error,
          `An error occurred while ${
            isEditing ? "updating" : "creating"
          } this integration's secret.  Please try again.`,
        );
        messageApi.error(secretsErrorMsg);
        return;
      }
    }

    // Save property assignments if editing
    if (isEditing && values.property_ids) {
      try {
        await savePropertyAssignments(values.property_ids);
      } catch {
        messageApi.error(PROPERTY_UPDATE_FAILED_MSG);
      }
    }

    messageApi.success(
      `Integration secret ${isEditing ? "updated" : "created"} successfully`,
    );

    // If a system is provided, link it to the integration
    if (values.system_fides_key && connectionPayload.key) {
      try {
        await setSystemLinks({
          connectionKey: connectionPayload.key,
          body: {
            links: [
              {
                system_fides_key: values.system_fides_key,
              },
            ],
          },
        }).unwrap();
      } catch (error) {
        // Log error but don't fail the form submission
        // eslint-disable-next-line no-console
        console.error("Failed to link system:", error);
        messageApi.error(
          "Failed to link this integration to a system.  The integration was saved, please try again.",
        );
      }
    }

    onClose();

    // Redirect to the newly created integration detail page
    if (!isEditing) {
      router.push({
        pathname: INTEGRATION_DETAIL_ROUTE,
        query: {
          id: connectionPayload.key,
        },
      });
    }

    if (
      connectionPayload &&
      values.dataset &&
      connectionOption.identifier === ConnectionType.DATAHUB
    ) {
      await patchConnectionDatasetConfig(values, connectionPayload.key, {
        showSuccessAlert: false,
      });
    }
  };

  const loading = secretsIsLoading || patchIsLoading || systemPatchIsLoading;

  // Form state tracking for parent component
  const allValues = Form.useWatch([], form);
  const [submittable, setSubmittable] = useState(false);
  const isDirty = form.isFieldsTouched();

  useEffect(() => {
    form
      .validateFields({ validateOnly: true })
      .then(() => setSubmittable(true))
      .catch(() => setSubmittable(false));
  }, [form, allValues]);

  useEffect(() => {
    if (onFormStateChange) {
      onFormStateChange({
        dirty: isDirty,
        isValid: submittable,
        submitForm: () => form.submit(),
        loading,
      });
    }
  }, [isDirty, submittable, loading, form, onFormStateChange]);

  if (secretsSchemaIsLoading) {
    return <Spin />;
  }

  const generateFields = (secretsSchema: ConnectionTypeSecretSchemaResponse) =>
    Object.entries(secretsSchema.properties).map(([fieldKey, fieldInfo]) => {
      const fieldName = `secrets.${fieldKey}`;
      return (
        <FormFieldFromSchema
          key={fieldName}
          name={fieldName}
          fieldSchema={fieldInfo}
          isRequired={secretsSchema.required.includes(fieldKey)}
          secretsSchema={secretsSchema}
          validate={getFieldValidation(fieldKey, fieldInfo)}
        />
      );
    });

  return (
    <>
      {description && (
        <Card className="mt-4">
          <Text>{description}</Text>
        </Card>
      )}
      <Form
        form={form}
        layout="vertical"
        initialValues={initialValues}
        onFinish={handleSubmit}
        key={connection?.key ?? "create"}
      >
        <Flex vertical className="mt-4">
          <Form.Item
            name="name"
            label="Name"
            rules={[{ required: true, message: "Name is required" }]}
            className="w-full"
          >
            <Input data-testid="input-name" />
          </Form.Item>
          <Form.Item name="description" label="Description" className="w-full">
            <Input data-testid="input-description" />
          </Form.Item>
          {connectionOption.identifier !== ConnectionType.MANUAL_TASK &&
            connectionOption.identifier !== ConnectionType.JIRA_TICKET &&
            connectionOption.identifier !== ConnectionType.WEBSITE && (
              <Form.Item
                name="system_fides_key"
                label="System"
                tooltip="Link this integration to a system for monitoring purposes"
                className="w-full"
              >
                <Select
                  aria-label="System"
                  data-testid="controlled-select-system_fides_key"
                  options={systemOptions}
                  onSearch={onSystemSearch}
                  filterOption={false}
                  loading={isFetchingSystems}
                  allowClear
                  placeholder="Search for a system..."
                  showSearch
                />
              </Form.Item>
            )}
          {hasSecrets && secrets && generateFields(secrets)}
          {isEditing && hasPlus && hasDatasets && (
            <Form.Item
              name="property_ids"
              label="Properties"
              tooltip="Assign properties to this integration's datasets to scope privacy request processing"
              className="w-full"
            >
              <Select
                aria-label="Properties"
                mode="multiple"
                options={propertyOptions}
                loading={isLoadingProperties}
                allowClear
                placeholder="Select properties..."
              />
            </Form.Item>
          )}
          {connectionOption.identifier === ConnectionType.DATAHUB && (
            <Form.Item
              name="dataset"
              label="Datasets"
              tooltip="Only BigQuery datasets are supported. Selected datasets will sync with matching DataHub datasets. If none are selected, all datasets will be included by default."
              className="w-full"
            >
              <Select
                aria-label="Datasets"
                data-testid="controlled-select-dataset"
                options={datasetOptions ?? []}
                mode="multiple"
              />
            </Form.Item>
          )}
        </Flex>
      </Form>
    </>
  );
};
