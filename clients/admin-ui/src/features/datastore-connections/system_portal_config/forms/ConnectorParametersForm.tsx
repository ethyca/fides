import {
  Button,
  ButtonGroup,
  CircleHelpIcon,
  Flex,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Input,
  isNumeric,
  NumberDecrementStepper,
  NumberIncrementStepper,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  Tooltip,
  VStack,
} from "@fidesui/react";
import { Option } from "common/form/inputs";
import { useAPIHelper } from "common/hooks";
import {
  ConnectionTypeSecretSchemaProperty,
  ConnectionTypeSecretSchemaReponse,
} from "connection-type/types";
import { useLazyGetDatastoreConnectionStatusQuery } from "datastore-connections/datastore-connection.slice";
import DSRCustomizationModal from "datastore-connections/system_portal_config/forms/DSRCustomizationForm/DSRCustomizationModal";
import { Field, FieldInputProps, Form, Formik, FormikProps } from "formik";
import React, { useEffect, useRef } from "react";

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

type ConnectorParametersFormProps = {
  secretsSchema?: ConnectionTypeSecretSchemaReponse;
  defaultValues: ConnectionConfigFormValues;
  isSubmitting: boolean;
  /**
   * Parent callback when Save is clicked
   */
  onSaveClick: (values: any, actions: any) => void;
  /**
   * Parent callback when Test Connection is clicked
   */
  onTestConnectionClick: (value: any) => void;
  /**
   * Text for the test button. Defaults to "Test connection"
   */
  testButtonLabel?: string;
  connectionConfig?: ConnectionConfigurationResponse;
  connectionOption: ConnectionSystemTypeMap;
  isCreatingConnectionConfig: boolean;
  datasetDropdownOptions: Option[];
  onDelete: (id: string) => void;
  deleteResult: any;
};

const ConnectorParametersForm: React.FC<ConnectorParametersFormProps> = ({
  secretsSchema,
  defaultValues,
  isSubmitting = false,
  onSaveClick,
  onTestConnectionClick,
  testButtonLabel = "Test integration",
  connectionOption,
  connectionConfig,
  datasetDropdownOptions,
  isCreatingConnectionConfig,
  onDelete,
  deleteResult,
}) => {
  const mounted = useRef(false);
  const { handleError } = useAPIHelper();

  const [trigger, result] = useLazyGetDatastoreConnectionStatusQuery();

  const validateConnectionIdentifier = (value: string) => {
    let error;
    if (typeof value === "undefined" || value === "") {
      error = "Integration Identifier is required";
    }
    if (value && isNumeric(value)) {
      error = "Integration Identifier must be an alphanumeric value";
    }
    return error;
  };

  const validateField = (label: string, value: string, type?: string) => {
    let error;
    if (typeof value === "undefined" || value === "") {
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

  const getFormField = (
    key: string,
    item: ConnectionTypeSecretSchemaProperty
  ): JSX.Element => (
    <Field
      id={key}
      name={key}
      key={key}
      validate={
        isRequiredSecretValue(key) || item.type === "integer"
          ? (value: string) =>
              validateField(item.title, value, item.allOf?.[0].$ref)
          : false
      }
    >
      {({ field, form }: { field: FieldInputProps<string>; form: any }) => (
        <FormControl
          display="flex"
          isRequired={isRequiredSecretValue(key)}
          isInvalid={form.errors[key] && form.touched[key]}
        >
          {getFormLabel(key, item.title)}
          <VStack align="flex-start" w="inherit">
            {item.type !== "integer" && (
              <Input
                {...field}
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
                defaultValue={0}
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
            <FormErrorMessage>{form.errors[key]}</FormErrorMessage>
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
              <CircleHelpIcon marginLeft="8px" _hover={{ cursor: "pointer" }} />
            </Flex>
          </Tooltip>
        </FormControl>
      )}
    </Field>
  );

  const getInitialValues = () => {
    const initialValues = { ...defaultValues };
    if (connectionConfig?.key) {
      initialValues.name = connectionConfig.name;
      initialValues.description = connectionConfig.description as string;
      initialValues.instance_key =
        connectionConfig.connection_type === ConnectionType.SAAS
          ? (connectionConfig.saas_config?.fides_key as string)
          : connectionConfig.key;
    }
    return fillInDefaults(initialValues, secretsSchema);
  };

  const handleSubmit = (values: any, actions: any) => {
    // convert each property value of type FidesopsDatasetReference
    // from a dot delimited string to a FidesopsDatasetReference
    const updatedValues = { ...values };
    if (secretsSchema) {
      Object.keys(secretsSchema.properties).forEach((key) => {
        if (
          secretsSchema.properties[key].allOf?.[0].$ref ===
          FIDES_DATASET_REFERENCE
        ) {
          const referencePath = values[key].split(".");
          updatedValues[key] = {
            dataset: referencePath.shift(),
            field: referencePath.join("."),
            direction: "from",
          };
        }
      });
    }
    onSaveClick(updatedValues, actions);
  };

  const handleTestConnectionClick = async () => {
    try {
      await trigger(connectionConfig!.key).unwrap();
    } catch (error) {
      handleError(error);
    }
  };

  const isRequiredSecretValue = (key: string): boolean =>
    secretsSchema?.required?.includes(key) ||
    (secretsSchema?.properties?.[key] !== undefined &&
      "default" in secretsSchema.properties[key]);

  useEffect(() => {
    mounted.current = true;
    if (result.isSuccess) {
      onTestConnectionClick(result);
    }
    return () => {
      mounted.current = false;
    };
  }, [onTestConnectionClick, result]);

  return (
    <Formik
      enableReinitialize
      initialValues={getInitialValues()}
      onSubmit={handleSubmit}
      validateOnBlur={false}
      validateOnChange={false}
    >
      {/* @ts-ignore */}
      {(props: FormikProps<Values>) => (
        <Form noValidate>
          <VStack align="stretch" gap="16px">
            {/* Connection Identifier */}
            {connectionOption.type !== SystemType.MANUAL ? (
              <Field
                id="instance_key"
                name="instance_key"
                validate={validateConnectionIdentifier}
              >
                {({ field }: { field: FieldInputProps<string> }) => (
                  <FormControl
                    display="flex"
                    isRequired
                    isInvalid={
                      props.errors.instance_key && props.touched.instance_key
                    }
                  >
                    {getFormLabel("instance_key", "Integration Identifier")}
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
            ) : null}
            {/* Dynamic connector secret fields */}

            {connectionOption.type !== SystemType.MANUAL && secretsSchema
              ? Object.entries(secretsSchema.properties).map(([key, item]) => {
                  if (key === "advanced_settings") {
                    // TODO: advanced settings
                    return null;
                  }
                  return getFormField(key, item);
                })
              : null}
            {SystemType.DATABASE === connectionOption.type &&
            !isCreatingConnectionConfig ? (
              <DatasetConfigField
                dropdownOptions={datasetDropdownOptions}
                connectionConfig={connectionConfig}
              />
            ) : null}
            <ButtonGroup size="sm" spacing="8px" variant="outline">
              <Button
                colorScheme="gray.700"
                isDisabled={
                  !connectionConfig?.key ||
                  isSubmitting ||
                  deleteResult.isLoading
                }
                isLoading={result.isLoading || result.isFetching}
                loadingText="Testing"
                onClick={handleTestConnectionClick}
                variant="outline"
              >
                {testButtonLabel}
              </Button>
              {connectionOption.type === SystemType.MANUAL &&
              connectionConfig ? (
                <DSRCustomizationModal connectionConfig={connectionConfig} />
              ) : null}
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
              {connectionConfig ? (
                <DeleteConnectionModal
                  connectionKey={connectionConfig.key}
                  onDelete={onDelete}
                  deleteResult={deleteResult}
                />
              ) : null}
            </ButtonGroup>
          </VStack>
        </Form>
      )}
    </Formik>
  );
};

export default ConnectorParametersForm;
