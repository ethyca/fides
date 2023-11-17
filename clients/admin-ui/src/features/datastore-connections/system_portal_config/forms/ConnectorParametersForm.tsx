import {
  Box,
  Button,
  ButtonGroup,
  CircleHelpIcon,
  Flex,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Input,
  NumberDecrementStepper,
  NumberIncrementStepper,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  Spacer,
  Tooltip,
  VStack,
} from "@fidesui/react";
import { Option, SelectInput } from "common/form/inputs";
import {
  ConnectionTypeSecretSchemaProperty,
  ConnectionTypeSecretSchemaReponse,
} from "connection-type/types";
import { useLazyGetDatastoreConnectionStatusQuery } from "datastore-connections/datastore-connection.slice";
import DSRCustomizationModal from "datastore-connections/system_portal_config/forms/DSRCustomizationForm/DSRCustomizationModal";
import { Field, FieldInputProps, Form, Formik, FormikProps } from "formik";
import _ from "lodash";
import React from "react";
import { DatastoreConnectionStatus } from "src/features/datastore-connections/types";

import { useFeatures } from "~/features/common/features";
import DisableConnectionModal from "~/features/datastore-connections/DisableConnectionModal";
import DatasetConfigField from "~/features/datastore-connections/system_portal_config/forms/fields/DatasetConfigField/DatasetConfigField";
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
  secretsSchema?: ConnectionTypeSecretSchemaReponse;
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
   * Text for the test button. Defaults to "Test connection"
   */
  testButtonLabel?: string;
  /**
   * Parent callback when Authorize Connection is clicked
   */
  onAuthorizeConnectionClick: (values: ConnectionConfigFormValues) => void;
  connectionConfig?: ConnectionConfigurationResponse;
  connectionOption: ConnectionSystemTypeMap;
  isCreatingConnectionConfig: boolean;
  datasetDropdownOptions: Option[];
  onDelete: () => void;
  deleteResult: any;
};

const ConnectorParametersForm: React.FC<ConnectorParametersFormProps> = ({
  secretsSchema,
  defaultValues,
  isSubmitting = false,
  isAuthorizing = false,
  onSaveClick,
  onTestConnectionClick,
  onAuthorizeConnectionClick,
  testButtonLabel = "Test integration",
  connectionOption,
  connectionConfig,
  datasetDropdownOptions,
  isCreatingConnectionConfig,
  onDelete,
  deleteResult,
}) => {
  const [trigger, { isLoading, isFetching }] =
    useLazyGetDatastoreConnectionStatusQuery();
  const { plus: isPlusEnabled } = useFeatures();

  const validateField = (label: string, value: string, type?: string) => {
    let error;
    if (typeof value === "undefined" || value === "" || value === undefined) {
      error = `${label} is required`;
    }
    if (type === FIDES_DATASET_REFERENCE) {
      if (!value.includes(".")) {
        error = "Dataset reference must be dot delimited";
      } else {
        const parts = value.split(".");
        if (parts.length < 3) {
          error = "Dataset reference must include at least three parts";
        }
      }
    }
    return error;
  };

  const getFormLabel = (id: string, value: string): JSX.Element => (
    <FormLabel
      color="gray.900"
      fontSize="14px"
      fontWeight="semibold"
      htmlFor={id}
      minWidth="150px"
    >
      {value}
    </FormLabel>
  );

  const getPlaceholder = (item: ConnectionTypeSecretSchemaProperty) => {
    if (item.allOf?.[0].$ref === FIDES_DATASET_REFERENCE) {
      return "Enter dataset.collection.field";
    }
    return undefined;
  };

  const isRequiredSecretValue = (key: string): boolean =>
    secretsSchema?.required?.includes(key) ||
    (secretsSchema?.properties?.[key] !== undefined &&
      "default" in secretsSchema.properties[key]);

  const getFormField = (
    key: string,
    item: ConnectionTypeSecretSchemaProperty
  ): JSX.Element => (
    <Field
      id={`secrets.${key}`}
      name={`secrets.${key}`}
      key={`secrets.${key}`}
      validate={
        isRequiredSecretValue(key) || item.type === "integer"
          ? (value: string) =>
              validateField(item.title, value, item.allOf?.[0].$ref)
          : false
      }
    >
      {({ field, form }: { field: FieldInputProps<string>; form: any }) => {
        const error = form.errors.secrets && form.errors.secrets[key];
        const touch = form.touched.secrets ? form.touched.secrets[key] : false;

        return (
          <FormControl
            display="flex"
            isRequired={isRequiredSecretValue(key)}
            isInvalid={error && touch}
          >
            {getFormLabel(key, item.title)}
            <VStack align="flex-start" w="inherit">
              {item.type !== "integer" && (
                <Input
                  {...field}
                  type={item.sensitive ? "password" : "text"}
                  placeholder={getPlaceholder(item)}
                  autoComplete="off"
                  color="gray.700"
                  size="sm"
                />
              )}
              {item.type === "integer" && (
                <NumberInput
                  allowMouseWheel
                  color="gray.700"
                  onChange={(value) => {
                    form.setFieldValue(field.name, value);
                  }}
                  value={field.value ?? 0}
                  min={0}
                  size="sm"
                >
                  <NumberInputField {...field} autoComplete="off" />
                  <NumberInputStepper>
                    <NumberIncrementStepper />
                    <NumberDecrementStepper />
                  </NumberInputStepper>
                </NumberInput>
              )}
              <FormErrorMessage>{error}</FormErrorMessage>
            </VStack>
            <Tooltip
              aria-label={item.description}
              hasArrow
              label={item.description}
              placement="right-start"
              openDelay={500}
            >
              <Flex
                alignItems="center"
                h="32px"
                visibility={item.description ? "visible" : "hidden"}
              >
                <CircleHelpIcon
                  marginLeft="8px"
                  _hover={{ cursor: "pointer" }}
                />
              </Flex>
            </Tooltip>
          </FormControl>
        );
      }}
    </Field>
  );

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
      initialValues.secrets = { ...connectionConfig.secrets };

      // check if we need we need to pre-process any secrets values
      // we currently only need to do this for Fides dataset references
      // to convert them from objects to dot-delimited strings
      if (secretsSchema?.properties) {
        Object.entries(secretsSchema.properties).forEach(([key, schema]) => {
          if (schema.allOf?.[0].$ref === FIDES_DATASET_REFERENCE) {
            const datasetReference = initialValues.secrets[key];
            initialValues.secrets[
              key
            ] = `${datasetReference.dataset}.${datasetReference.field}`;
          }
        });
      }

      return initialValues;
    }

    if (_.isEmpty(initialValues.enabled_actions)) {
      initialValues.enabled_actions = connectionOption.supported_actions.map(
        (action) => action.toString()
      );
    }

    return fillInDefaults(initialValues, secretsSchema);
  };

  /**
   * Preprocesses the input values.
   * Currently, it is only used to convert FIDES_DATASET_REFERENCE fields.
   * @param values ConnectionConfigFormValues - The original values.
   * @returns ConnectionConfigFormValues - The processed values.
   */
  const preprocessValues = (
    values: ConnectionConfigFormValues
  ): ConnectionConfigFormValues => {
    const updatedValues = _.cloneDeep(values);
    if (secretsSchema) {
      Object.keys(secretsSchema.properties).forEach((key) => {
        if (
          secretsSchema.properties[key].allOf?.[0].$ref ===
          FIDES_DATASET_REFERENCE
        ) {
          const referencePath = updatedValues.secrets[key].split(".");
          updatedValues.secrets[key] = {
            dataset: referencePath.shift(),
            field: referencePath.join("."),
            direction: "from",
          };
        }
      });
    }
    return updatedValues;
  };

  const handleSubmit = (values: any, actions: any) => {
    // convert each property value of type FidesopsDatasetReference
    // from a dot delimited string to a FidesopsDatasetReference
    const processedValues = preprocessValues(values);
    onSaveClick(processedValues, actions);
  };

  const handleAuthorizeConnectionClick = async (
    values: ConnectionConfigFormValues,
    props: FormikProps<ConnectionConfigFormValues>
  ) => {
    const errors = await props.validateForm();

    if (Object.keys(errors).length > 0) {
      return;
    }

    const processedValues = preprocessValues(values);
    onAuthorizeConnectionClick(processedValues);
  };

  const handleTestConnectionClick = async (
    props: FormikProps<ConnectionConfigFormValues>
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
      validateOnBlur={false}
      validateOnChange={false}
    >
      {(props: FormikProps<ConnectionConfigFormValues>) => {
        const authorized = !props.dirty && connectionConfig?.authorized;
        return (
          <Form noValidate>
            <VStack align="stretch" gap="16px">
              <ButtonGroup size="sm" spacing="8px" variant="outline">
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
              </ButtonGroup>
              {/* Connection Identifier */}
              {!!connectionConfig?.key && (
                <Field id="instance_key" name="instance_key">
                  {({ field }: { field: FieldInputProps<string> }) => (
                    <FormControl display="flex">
                      {getFormLabel("instance_key", "Integration identifier")}
                      <VStack align="flex-start" w="inherit">
                        <Input
                          {...field}
                          autoComplete="off"
                          color="gray.700"
                          isDisabled={!!connectionConfig?.key}
                          placeholder={`A unique identifier for your new ${
                            connectionOption!.human_readable
                          } integration`}
                          size="sm"
                        />
                        <FormErrorMessage>
                          {props.errors.instance_key}
                        </FormErrorMessage>
                      </VStack>
                      <Tooltip
                        aria-label="The fides_key will allow fidesops to associate dataset field references appropriately. Must be a unique alphanumeric value with no spaces (underscores allowed) to represent this integration."
                        hasArrow
                        label="The fides_key will allow fidesops to associate dataset field references appropriately. Must be a unique alphanumeric value with no spaces (underscores allowed) to represent this integration."
                        placement="right-start"
                        openDelay={500}
                      >
                        <Flex alignItems="center" h="32px">
                          <CircleHelpIcon
                            marginLeft="8px"
                            _hover={{ cursor: "pointer" }}
                          />
                        </Flex>
                      </Tooltip>
                    </FormControl>
                  )}
                </Field>
              )}
              {/* Dynamic connector secret fields */}
              {connectionOption.type !== SystemType.MANUAL && secretsSchema
                ? Object.entries(secretsSchema.properties).map(
                    ([key, item]) => {
                      if (key === "advanced_settings") {
                        // TODO: advanced settings
                        return null;
                      }
                      return getFormField(key, item);
                    }
                  )
                : null}
              {isPlusEnabled && (
                <Field
                  id="enabled_actions"
                  name="enabled_actions"
                  validate={(value: string[]) => {
                    let error;
                    if (!value || value.length === 0) {
                      error = "At least one request type must be selected";
                    }
                    return error;
                  }}
                >
                  {({
                    field,
                    form,
                  }: {
                    field: FieldInputProps<string>;
                    form: any;
                  }) => (
                    <FormControl
                      data-testid="enabled-actions"
                      display="flex"
                      isInvalid={
                        form.touched.enabled_actions &&
                        form.errors.enabled_actions
                      }
                      isRequired
                    >
                      {/* Known as enabled_actions throughout the front-end and back-end but it's displayed to the user as "Request types" */}
                      {getFormLabel("enabled_actions", "Request types")}
                      <VStack align="flex-start" w="inherit">
                        <Box width="100%">
                          <SelectInput
                            options={connectionOption.supported_actions.map(
                              (action) => ({
                                label: _.upperFirst(action),
                                value: action,
                              })
                            )}
                            fieldName={field.name}
                            size="sm"
                            isMulti
                            isDisabled={
                              connectionOption.supported_actions.length === 1
                            }
                          />
                        </Box>
                        <FormErrorMessage>
                          {props.errors.enabled_actions}
                        </FormErrorMessage>
                      </VStack>
                      <Tooltip
                        aria-label="The request types that are supported for this integration."
                        hasArrow
                        label="The request types that are supported for this integration."
                        placement="right-start"
                        openDelay={500}
                      >
                        <Flex alignItems="center" h="32px">
                          <CircleHelpIcon
                            marginLeft="8px"
                            _hover={{ cursor: "pointer" }}
                          />
                        </Flex>
                      </Tooltip>
                    </FormControl>
                  )}
                </Field>
              )}
              {SystemType.DATABASE === connectionOption.type &&
              !isCreatingConnectionConfig ? (
                <DatasetConfigField
                  dropdownOptions={datasetDropdownOptions}
                  connectionConfig={connectionConfig}
                />
              ) : null}
              <ButtonGroup size="sm" spacing="8px" variant="outline">
                {!connectionOption.authorization_required || authorized ? (
                  <Button
                    colorScheme="gray.700"
                    isDisabled={
                      !connectionConfig?.key ||
                      isSubmitting ||
                      deleteResult.isLoading
                    }
                    isLoading={isLoading || isFetching}
                    loadingText="Testing"
                    onClick={() => handleTestConnectionClick(props)}
                    variant="outline"
                  >
                    {testButtonLabel}
                  </Button>
                ) : null}
                {connectionOption.authorization_required && !authorized ? (
                  <Button
                    colorScheme="gray.700"
                    isLoading={isAuthorizing}
                    loadingText="Authorizing"
                    onClick={() =>
                      handleAuthorizeConnectionClick(props.values, props)
                    }
                    variant="outline"
                  >
                    Authorize integration
                  </Button>
                ) : null}
                {connectionOption.type === SystemType.MANUAL ? (
                  <DSRCustomizationModal connectionConfig={connectionConfig} />
                ) : null}
                <Spacer />
                <Button
                  bg="primary.800"
                  color="white"
                  isDisabled={deleteResult.isLoading || isSubmitting}
                  isLoading={isSubmitting}
                  loadingText="Submitting"
                  size="sm"
                  variant="solid"
                  type="submit"
                  _active={{ bg: "primary.500" }}
                  _hover={{ bg: "primary.400" }}
                >
                  Save
                </Button>
              </ButtonGroup>
            </VStack>
          </Form>
        );
      }}
    </Formik>
  );
};

export default ConnectorParametersForm;
