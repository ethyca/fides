import type { Option } from "common/form/inputs";
import { ConnectionTypeSecretSchemaResponse } from "connection-type/types";
import { useLazyGetDatastoreConnectionStatusQuery } from "datastore-connections/datastore-connection.slice";
import DSRCustomizationModal from "datastore-connections/system_portal_config/forms/DSRCustomizationForm/DSRCustomizationModal";
import { Button, Flex, Form, Input, Select } from "fidesui";
import _ from "lodash";
import React, { useMemo } from "react";
import { DatastoreConnectionStatus } from "src/features/datastore-connections/types";

import { useFeatures } from "~/features/common/features";
import { FormFieldFromSchema } from "~/features/common/form/FormFieldFromSchema";
import {
  FIDES_DATASET_REFERENCE,
  useFormFieldsFromSchema,
} from "~/features/common/form/useFormFieldsFromSchema";
import DatasetSelectOption from "~/features/dataset/DatasetSelectOption";
import DisableConnectionModal from "~/features/datastore-connections/DisableConnectionModal";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  ConnectionType,
  SystemType,
} from "~/types/api";

import DeleteConnectionModal from "../DeleteConnectionModal";
import { ConnectionConfigFormValues } from "../types";
import { fillInDefaults } from "./helpers";

export interface TestConnectionResponse {
  data?: DatastoreConnectionStatus;
  fulfilledTimeStamp?: number;
}

type ConnectorParametersFormProps = {
  secretsSchema?: ConnectionTypeSecretSchemaResponse;
  defaultValues: ConnectionConfigFormValues;
  isSubmitting: boolean;
  isAuthorizing: boolean;
  /**
   * Parent callback when Save is clicked
   */
  onSaveClick: (values: any, actions: any) => void;
  /**
   * Parent callback when Test Connection is clicked
   */
  onTestConnectionClick: (value: TestConnectionResponse) => void;
  /**
   * Parent callback when Test Dataset is clicked
   */
  onTestDatasetsClick: () => void;
  /**
   * Text for the test button. Defaults to "Test connection"
   */
  testButtonLabel?: string;
  /**
   * Parent callback when Authorize Connection is clicked
   */
  onAuthorizeConnectionClick: (values: ConnectionConfigFormValues) => void;
  connectionConfig?: ConnectionConfigurationResponse | null;
  connectionOption: ConnectionSystemTypeMap;
  isCreatingConnectionConfig: boolean;
  initialDatasets?: string[];
  datasetDropdownOptions: Option[];
  onDelete: () => void;
  deleteResult: any;
};

export const ConnectorParametersForm = ({
  secretsSchema,
  defaultValues,
  isSubmitting = false,
  isAuthorizing = false,
  onSaveClick,
  onTestConnectionClick,
  onTestDatasetsClick,
  onAuthorizeConnectionClick,
  testButtonLabel = "Test integration",
  connectionOption,
  connectionConfig,
  initialDatasets,
  datasetDropdownOptions,
  isCreatingConnectionConfig,
  onDelete,
  deleteResult,
}: ConnectorParametersFormProps) => {
  const [trigger, { isLoading, isFetching }] =
    useLazyGetDatastoreConnectionStatusQuery();
  const { plus: isPlusEnabled } = useFeatures();

  const { getFieldValidation, preprocessValues } =
    useFormFieldsFromSchema(secretsSchema);

  const [form] = Form.useForm<ConnectionConfigFormValues>();

  const initialFormValues = useMemo(() => {
    const values = { ...defaultValues };
    if (connectionConfig?.key) {
      values.name = connectionConfig.name ?? "";
      values.description = connectionConfig.description as string;
      values.instance_key =
        connectionConfig.connection_type === ConnectionType.SAAS
          ? (connectionConfig.saas_config?.fides_key as string)
          : connectionConfig.key;
      values.enabled_actions = (connectionConfig.enabled_actions || []).map(
        (action) => action.toString(),
      );

      values.secrets = connectionConfig.secrets
        ? _.cloneDeep(connectionConfig.secrets)
        : {};

      values.dataset = initialDatasets;

      // check if we need we need to pre-process any secrets values
      // we currently only need to do this for Fides dataset references
      // to convert them from objects to dot-delimited strings
      if (secretsSchema?.properties) {
        Object.entries(secretsSchema.properties).forEach(([key, schema]) => {
          if (schema.allOf?.[0].$ref === FIDES_DATASET_REFERENCE) {
            const datasetReference = values.secrets[key];
            if (datasetReference) {
              values.secrets[key] =
                `${datasetReference.dataset}.${datasetReference.field}`;
            }
          }
          // Convert boolean secret values to string so they correctly match ControlledSelect options
          if (secretsSchema.properties[key]?.type === "boolean") {
            const boolVal = values.secrets[key];
            if (typeof boolVal === "boolean") {
              values.secrets[key] = boolVal.toString();
            }
          }
        });
      }
      return values;
    }

    if (_.isEmpty(values.enabled_actions)) {
      values.enabled_actions = connectionOption.supported_actions.map(
        (action) => action.toString(),
      );
    }

    return fillInDefaults(values, secretsSchema);
  }, [
    connectionConfig,
    defaultValues,
    secretsSchema,
    initialDatasets,
    connectionOption,
  ]);

  const handleFinish = (values: ConnectionConfigFormValues) => {
    const processedValues = preprocessValues(values);
    onSaveClick(processedValues, { setSubmitting: () => {} });
  };

  const handleAuthorizeConnectionClick = async () => {
    try {
      await form.validateFields();
    } catch {
      return;
    }
    const processedValues = preprocessValues(form.getFieldsValue(true));
    onAuthorizeConnectionClick(processedValues);
  };

  const handleTestConnectionClick = async () => {
    try {
      await form.validateFields();
    } catch {
      return;
    }
    const result = await trigger(connectionConfig!.key);
    onTestConnectionClick(result);
  };

  const isDisabledConnection = connectionConfig?.disabled || false;

  const allValues = Form.useWatch([], form);
  const isDirty = useMemo(
    () => !_.isEqual(allValues, initialFormValues),
    [allValues, initialFormValues],
  );
  const authorized = !isDirty && connectionConfig?.authorized;

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={initialFormValues}
      onFinish={handleFinish}
      key={connectionConfig?.key ?? "create"}
      validateTrigger="onBlur"
    >
      <Flex vertical gap={16}>
        {/* Hidden fields to preserve values in form submission */}
        <Form.Item name="name" hidden noStyle>
          <input type="hidden" />
        </Form.Item>
        <Form.Item name="description" hidden noStyle>
          <input type="hidden" />
        </Form.Item>
        <div className="flex flex-row">
          {connectionConfig ? (
            <DisableConnectionModal
              connection_key={connectionConfig?.key}
              disabled={isDisabledConnection}
              connection_type={connectionConfig?.connection_type}
              access_type={connectionConfig?.access}
              name={connectionConfig?.name ?? connectionConfig.key}
            />
          ) : null}
          {connectionConfig ? (
            <DeleteConnectionModal
              onDelete={onDelete}
              deleteResult={deleteResult}
            />
          ) : null}
        </div>
        {/* Connection Identifier */}
        {!!connectionConfig?.key && (
          <Form.Item
            name="instance_key"
            label="Integration identifier"
            tooltip="The fides_key will allow fidesops to associate dataset field references appropriately. Must be a unique alphanumeric value with no spaces (underscores allowed) to represent this integration."
            rules={[{ required: true }]}
            layout="horizontal"
          >
            <Input
              data-testid="input-instance_key"
              disabled={!!connectionConfig?.key}
            />
          </Form.Item>
        )}
        {/* Dynamic connector secret fields */}
        {secretsSchema
          ? Object.entries(secretsSchema.properties).map(([key, item]) => {
              if (key === "advanced_settings") {
                // TODO: advanced settings
                return null;
              }
              return (
                <FormFieldFromSchema
                  key={`secrets.${key}`}
                  name={`secrets.${key}`}
                  fieldSchema={item}
                  isRequired={secretsSchema.required?.includes(key)}
                  secretsSchema={secretsSchema}
                  validate={getFieldValidation(key, item)}
                  layout="inline"
                />
              );
            })
          : null}
        {isPlusEnabled ? (
          <Form.Item
            name="enabled_actions"
            label="Request types"
            tooltip="The request types that are supported for this integration"
            rules={[{ required: true }]}
            layout="horizontal"
          >
            <Select
              aria-label="Request types"
              data-testid="controlled-select-enabled_actions"
              mode="multiple"
              options={connectionOption.supported_actions.map((action) => ({
                label: _.upperFirst(action),
                value: action,
              }))}
            />
          </Form.Item>
        ) : (
          <Form.Item name="enabled_actions" hidden noStyle>
            <input type="hidden" />
          </Form.Item>
        )}
        {SystemType.DATABASE === connectionOption.type &&
          !isCreatingConnectionConfig && (
            <Form.Item
              name="dataset"
              label="Datasets"
              tooltip="Select datasets to associate with this integration"
              layout="horizontal"
            >
              <Select
                aria-label="Datasets"
                data-testid="controlled-select-dataset"
                mode="multiple"
                options={datasetDropdownOptions}
                optionRender={DatasetSelectOption}
              />
            </Form.Item>
          )}
        <div className="flex gap-4">
          {!connectionOption.authorization_required || authorized ? (
            <Button
              disabled={
                !connectionConfig?.key || isSubmitting || deleteResult.isLoading
              }
              loading={isLoading || isFetching}
              onClick={() => handleTestConnectionClick()}
              data-testid="test-connection-button"
            >
              {testButtonLabel}
            </Button>
          ) : null}
          {isPlusEnabled &&
            SystemType.DATABASE === connectionOption.type &&
            !_.isEmpty(initialDatasets) && (
              <Button onClick={() => onTestDatasetsClick()}>
                Test datasets
              </Button>
            )}
          {connectionOption.authorization_required && !authorized ? (
            <Button
              loading={isAuthorizing}
              onClick={() => handleAuthorizeConnectionClick()}
            >
              Authorize integration
            </Button>
          ) : null}
          {connectionOption.type === SystemType.MANUAL ? (
            <DSRCustomizationModal connectionConfig={connectionConfig} />
          ) : null}
          <div className="grow" />
          <Button
            type="primary"
            disabled={deleteResult.isLoading || isSubmitting}
            loading={isSubmitting}
            htmlType="submit"
            data-testid="save-integration-btn"
          >
            Save
          </Button>
        </div>
      </Flex>
    </Form>
  );
};
