import { CustomTextInput, Option } from "common/form/inputs";
import { ConnectionTypeSecretSchemaResponse } from "connection-type/types";
import { useLazyGetDatastoreConnectionStatusQuery } from "datastore-connections/datastore-connection.slice";
import DSRCustomizationModal from "datastore-connections/system_portal_config/forms/DSRCustomizationForm/DSRCustomizationModal";
import { AntButton as Button, Spacer, VStack } from "fidesui";
import { Form, Formik, FormikProps } from "formik";
import _ from "lodash";
import React from "react";
import { DatastoreConnectionStatus } from "src/features/datastore-connections/types";

import { useFeatures } from "~/features/common/features";
import { ControlledSelect } from "~/features/common/form/ControlledSelect";
import { FormFieldFromSchema } from "~/features/common/form/FormFieldFromSchema";
import { useFormFieldsFromSchema } from "~/features/common/form/useFormFieldsFromSchema";
import DisableConnectionModal from "~/features/datastore-connections/DisableConnectionModal";
import SelectDataset from "~/features/datastore-connections/system_portal_config/forms/SelectDataset";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  ConnectionType,
  SystemType,
} from "~/types/api";

import DeleteConnectionModal from "../DeleteConnectionModal";
import { ConnectionConfigFormValues } from "../types";
import { fillInDefaults } from "./helpers";

const FIDES_DATASET_REFERENCE = "#/definitions/FidesDatasetReference";

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

  const getInitialValues = () => {
    const initialValues = { ...defaultValues };
    if (connectionConfig?.key) {
      initialValues.name = connectionConfig.name ?? "";
      initialValues.description = connectionConfig.description as string;
      initialValues.instance_key =
        connectionConfig.connection_type === ConnectionType.SAAS
          ? (connectionConfig.saas_config?.fides_key as string)
          : connectionConfig.key;
      initialValues.enabled_actions = (
        connectionConfig.enabled_actions || []
      ).map((action) => action.toString());

      // @ts-ignore
      initialValues.secrets = connectionConfig.secrets
        ? _.cloneDeep(connectionConfig.secrets)
        : {};

      initialValues.dataset = initialDatasets;

      // check if we need we need to pre-process any secrets values
      // we currently only need to do this for Fides dataset references
      // to convert them from objects to dot-delimited strings
      if (secretsSchema?.properties) {
        Object.entries(secretsSchema.properties).forEach(([key, schema]) => {
          if (schema.allOf?.[0].$ref === FIDES_DATASET_REFERENCE) {
            const datasetReference = initialValues.secrets[key];
            if (datasetReference) {
              initialValues.secrets[key] =
                `${datasetReference.dataset}.${datasetReference.field}`;
            }
          }
        });
      }
      return initialValues;
    }

    if (_.isEmpty(initialValues.enabled_actions)) {
      initialValues.enabled_actions = connectionOption.supported_actions.map(
        (action) => action.toString(),
      );
    }

    return fillInDefaults(initialValues, secretsSchema);
  };

  const handleSubmit = (values: any, actions: any) => {
    const processedValues = preprocessValues(values);
    onSaveClick(processedValues, actions);
  };

  const handleAuthorizeConnectionClick = async (
    values: ConnectionConfigFormValues,
    props: FormikProps<ConnectionConfigFormValues>,
  ) => {
    const errors = await props.validateForm();

    if (Object.keys(errors).length > 0) {
      return;
    }

    const processedValues = preprocessValues(values);
    onAuthorizeConnectionClick(processedValues);
  };

  const handleTestConnectionClick = async (
    props: FormikProps<ConnectionConfigFormValues>,
  ) => {
    const errors = await props.validateForm();

    if (Object.keys(errors).length > 0) {
      return;
    }

    const result = await trigger(connectionConfig!.key);
    onTestConnectionClick(result);
  };

  const isDisabledConnection = connectionConfig?.disabled || false;

  return (
    <Formik
      enableReinitialize
      initialValues={getInitialValues()}
      onSubmit={handleSubmit}
      validateOnBlur
    >
      {(props) => {
        const authorized = !props.dirty && connectionConfig?.authorized;
        return (
          <Form>
            <VStack align="stretch" gap="16px">
              <div className="flex flex-row">
                {connectionConfig ? (
                  <DisableConnectionModal
                    connection_key={connectionConfig?.key}
                    disabled={isDisabledConnection}
                    connection_type={connectionConfig?.connection_type}
                    access_type={connectionConfig?.access}
                    name={connectionConfig?.name ?? connectionConfig.key}
                    isSwitch
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
                <CustomTextInput
                  name="instance_key"
                  key="instance_key"
                  id="instance_key"
                  label="Integration identifier"
                  isRequired
                  disabled={!!connectionConfig?.key}
                  tooltip="The fides_key will allow fidesops to associate dataset field references appropriately. Must be a unique alphanumeric value with no spaces (underscores allowed) to represent this integration."
                />
              )}
              {/* Dynamic connector secret fields */}
              {secretsSchema
                ? Object.entries(secretsSchema.properties).map(
                    ([key, item]) => {
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
                    },
                  )
                : null}
              {isPlusEnabled && (
                <ControlledSelect
                  name="enabled_actions"
                  key="enabled_actions"
                  id="enabled_actions"
                  label="Request types"
                  isRequired
                  layout="inline"
                  mode="multiple"
                  tooltip="The request types that are supported for this integration"
                  options={connectionOption.supported_actions.map((action) => ({
                    label: _.upperFirst(action),
                    value: action,
                  }))}
                />
              )}
              {SystemType.DATABASE === connectionOption.type &&
                !isCreatingConnectionConfig && (
                  // <SelectDataset options={datasetDropdownOptions} />
                  <ControlledSelect
                    name="dataset"
                    id="dataset"
                    tooltip="Select datasets to associate with this integration"
                    label="Datasets"
                    options={datasetDropdownOptions}
                    layout="inline"
                  />
                )}
              <div className="flex gap-4">
                {!connectionOption.authorization_required || authorized ? (
                  <Button
                    disabled={
                      !connectionConfig?.key ||
                      isSubmitting ||
                      deleteResult.isLoading
                    }
                    loading={isLoading || isFetching}
                    onClick={() => handleTestConnectionClick(props)}
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
                    onClick={() =>
                      handleAuthorizeConnectionClick(props.values, props)
                    }
                  >
                    Authorize integration
                  </Button>
                ) : null}
                {connectionOption.type === SystemType.MANUAL ? (
                  <DSRCustomizationModal connectionConfig={connectionConfig} />
                ) : null}
                <Spacer />
                <Button
                  type="primary"
                  disabled={deleteResult.isLoading || isSubmitting}
                  loading={isSubmitting}
                  htmlType="submit"
                >
                  Save
                </Button>
              </div>
            </VStack>
          </Form>
        );
      }}
    </Formik>
  );
};
