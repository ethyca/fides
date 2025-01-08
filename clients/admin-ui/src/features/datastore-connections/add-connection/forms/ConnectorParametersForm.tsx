import { useAPIHelper } from "common/hooks";
import { selectConnectionTypeState } from "connection-type/connection-type.slice";
import {
  ConnectionTypeSecretSchemaProperty,
  ConnectionTypeSecretSchemaResponse,
} from "connection-type/types";
import { useLazyGetDatastoreConnectionStatusQuery } from "datastore-connections/datastore-connection.slice";
import {
  AntButton as Button,
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
  Textarea,
  Tooltip,
  VStack,
} from "fidesui";
import { Field, FieldInputProps, Form, Formik, FormikProps } from "formik";
import React, { useEffect, useRef } from "react";

import { useAppSelector } from "~/app/hooks";
import { ConnectionType } from "~/types/api";

import {
  DatabaseConnectorParametersFormFields,
  SaasConnectorParametersFormFields,
} from "../types";
import { fillInDefaults } from "./helpers";

const FIDES_DATASET_REFERENCE = "#/definitions/FidesDatasetReference";

type ConnectorParametersFormProps = {
  data: ConnectionTypeSecretSchemaResponse;
  defaultValues:
    | DatabaseConnectorParametersFormFields
    | SaasConnectorParametersFormFields;
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
};

const ConnectorParametersForm = ({
  data,
  defaultValues,
  isSubmitting = false,
  onSaveClick,
  onTestConnectionClick,
  testButtonLabel = "Test integration",
}: ConnectorParametersFormProps) => {
  const mounted = useRef(false);
  const { handleError } = useAPIHelper();

  const { connection, connectionOption } = useAppSelector(
    selectConnectionTypeState,
  );

  const [trigger, result] = useLazyGetDatastoreConnectionStatusQuery();

  const validateConnectionIdentifier = (value: string) => {
    let error;
    if (typeof value === "undefined" || value === "") {
      error = "Connection Identifier is required";
    }
    if (value && isNumeric(value)) {
      error = "Connection Identifier must be an alphanumeric value";
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
    item: ConnectionTypeSecretSchemaProperty,
  ): JSX.Element => (
    <Field
      id={key}
      name={key}
      key={key}
      validate={
        data.required?.includes(key) || item.type === "integer"
          ? (value: string) =>
              validateField(item.title, value, item.allOf?.[0].$ref)
          : false
      }
    >
      {({ field, form }: { field: FieldInputProps<string>; form: any }) => (
        <FormControl
          display="flex"
          isRequired={data.required?.includes(key)}
          isInvalid={form.errors[key] && form.touched[key]}
        >
          {getFormLabel(key, item.title)}
          <VStack align="flex-start" w="inherit">
            {item.type !== "integer" && (
              <Input
                {...field}
                value={field.value || ""}
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
    if (connection?.key) {
      initialValues.name = connection.name ?? "";
      initialValues.description = connection.description as string;
      initialValues.instance_key =
        connection.connection_type === ConnectionType.SAAS
          ? (connection.saas_config?.fides_key as string)
          : connection.key;
    }
    return fillInDefaults(initialValues, data);
  };

  const handleSubmit = (values: any, actions: any) => {
    // convert each property value of type FidesopsDatasetReference
    // from a dot delimited string to a FidesopsDatasetReference
    const updatedValues = { ...values };
    Object.keys(data.properties).forEach((key) => {
      if (data.properties[key].allOf?.[0].$ref === FIDES_DATASET_REFERENCE) {
        const referencePath = values[key].split(".");
        updatedValues[key] = {
          dataset: referencePath.shift(),
          field: referencePath.join("."),
          direction: "from",
        };
      }
    });
    onSaveClick(updatedValues, actions);
  };

  const handleTestConnectionClick = async () => {
    try {
      await trigger(connection!.key).unwrap();
    } catch (error) {
      handleError(error);
    }
  };

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
            {/* Name */}
            <Field
              id="name"
              name="name"
              validate={(value: string) => validateField("Name", value)}
            >
              {({ field }: { field: FieldInputProps<string> }) => (
                <FormControl
                  display="flex"
                  isRequired
                  isInvalid={props.errors.name && props.touched.name}
                >
                  {getFormLabel("name", "Name")}
                  <VStack align="flex-start" w="inherit">
                    <Input
                      {...field}
                      autoComplete="off"
                      autoFocus
                      color="gray.700"
                      placeholder={`Enter a friendly name for your new ${
                        connectionOption!.human_readable
                      } connection`}
                      size="sm"
                      data-testid="input-name"
                    />
                    <FormErrorMessage>{props.errors.name}</FormErrorMessage>
                  </VStack>
                  <Flex alignItems="center" h="32px" visibility="hidden">
                    <CircleHelpIcon marginLeft="8px" />
                  </Flex>
                </FormControl>
              )}
            </Field>
            {/* Description */}
            <Field id="description" name="description">
              {({ field }: { field: FieldInputProps<string> }) => (
                <FormControl display="flex">
                  {getFormLabel("description", "Description")}
                  <Textarea
                    {...field}
                    color="gray.700"
                    placeholder={`Enter a description for your new ${
                      connectionOption!.human_readable
                    } connection`}
                    resize="none"
                    size="sm"
                    value={field.value || ""}
                  />
                  <Flex alignItems="center" h="32px" visibility="hidden">
                    <CircleHelpIcon marginLeft="8px" />
                  </Flex>
                </FormControl>
              )}
            </Field>
            {/* Connection Identifier */}
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
                  {getFormLabel("instance_key", "Connection Identifier")}
                  <VStack align="flex-start" w="inherit">
                    <Input
                      {...field}
                      autoComplete="off"
                      color="gray.700"
                      isDisabled={!!connection?.key}
                      placeholder={`A unique identifier for your new ${
                        connectionOption!.human_readable
                      } connection`}
                      size="sm"
                    />
                    <FormErrorMessage>
                      {props.errors.instance_key}
                    </FormErrorMessage>
                  </VStack>
                  <Tooltip
                    aria-label="The fides_key will allow fidesops to associate dataset field references appropriately. Must be a unique alphanumeric value with no spaces (underscores allowed) to represent this connection."
                    hasArrow
                    label="The fides_key will allow fidesops to associate dataset field references appropriately. Must be a unique alphanumeric value with no spaces (underscores allowed) to represent this connection."
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
            {/* Dynamic connector secret fields */}
            {Object.entries(data.properties).map(([key, item]) => {
              if (key === "advanced_settings") {
                // TODO: advanced settings
                return null;
              }
              return getFormField(key, item);
            })}
            <div className="flex gap-2">
              <Button
                disabled={!connection?.key}
                loading={result.isLoading || result.isFetching}
                onClick={handleTestConnectionClick}
              >
                {testButtonLabel}
              </Button>
              <Button
                htmlType="submit"
                type="primary"
                disabled={isSubmitting}
                loading={isSubmitting}
              >
                Save
              </Button>
            </div>
          </VStack>
        </Form>
      )}
    </Formik>
  );
};

export default ConnectorParametersForm;
