/* eslint-disable no-param-reassign */
import { isNumeric } from "@chakra-ui/utils";
import {
  Button,
  ButtonGroup,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Input,
  NumberDecrementStepper,
  NumberIncrementStepper,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  Textarea,
  Tooltip,
  VStack,
} from "@fidesui/react";
import { useAppSelector } from "app/hooks";
import { useAPIHelper } from "common/hooks";
import { CircleHelpIcon } from "common/Icon";
import { selectConnectionTypeState } from "connection-type/connection-type.slice";
import { ConnectionTypeSecretSchemaReponse } from "connection-type/types";
import { ConnectionType } from "datastore-connections/constants";
import { useLazyGetDatastoreConnectionStatusQuery } from "datastore-connections/datastore-connection.slice";
import { Field, Form, Formik, FormikProps } from "formik";
import React, { useEffect, useRef } from "react";

import {
  DatabaseConnectorParametersFormFields,
  SaasConnectorParametersFormFields,
} from "../types";

type ConnectorParametersFormProps = {
  data: ConnectionTypeSecretSchemaReponse;
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
};

const ConnectorParametersForm: React.FC<ConnectorParametersFormProps> = ({
  data,
  defaultValues,
  isSubmitting = false,
  onSaveClick,
  onTestConnectionClick,
}) => {
  const mounted = useRef(false);
  const { handleError } = useAPIHelper();

  const { connection, connectionOption } = useAppSelector(
    selectConnectionTypeState
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

  const validateField = (label: string, value: string) => {
    let error;
    if (typeof value === "undefined" || value === "") {
      error = `${label} is required`;
    }
    return error;
  };

  const getFormLabel = (id: string, value: string): JSX.Element => (
    <FormLabel
      color="gray.900"
      fontSize="14px"
      fontWeight="semibold"
      htmlFor={id}
      minWidth="141px"
    >
      {value}
    </FormLabel>
  );

  const getFormField = (
    key: string,
    item: { title: string; type: string }
  ): JSX.Element => (
    <Field
      id={key}
      name={key}
      key={key}
      validate={
        data.required?.includes(key) || item.type === "integer"
          ? (value: string) => validateField(item.title, value)
          : false
      }
    >
      {({ field, form }: { field: any; form: any }) => (
        <FormControl
          display="flex"
          isRequired={data.required?.includes(key)}
          isInvalid={form.errors[key] && form.touched[key]}
        >
          {getFormLabel(key, item.title)}
          <VStack align="flex-start" w="inherit">
            {item.type !== "integer" && (
              <Input {...field} autoComplete="off" color="gray.700" size="sm" />
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
          <CircleHelpIcon marginLeft="8px" visibility="hidden" />
        </FormControl>
      )}
    </Field>
  );

  const getInitialValues = () => {
    if (connection?.key) {
      defaultValues.name = connection.name;
      defaultValues.description = connection.description as string;
      defaultValues.instance_key =
        connection.connection_type === ConnectionType.SAAS
          ? (connection.saas_config?.fides_key as string)
          : connection.key;
      Object.entries(data.properties).forEach((key) => {
        // eslint-disable-next-line no-nested-ternary
        defaultValues[key[0]] = key[1].default
          ? key[1].default
          : key[1].type === "integer"
          ? 0
          : "";
      });
    } else {
      Object.entries(data.properties).forEach((key) => {
        // eslint-disable-next-line no-nested-ternary
        defaultValues[key[0]] = key[1].default
          ? key[1].default
          : key[1].type === "integer"
          ? 0
          : "";
      });
    }
    return defaultValues;
  };

  const handleSubmit = (values: any, actions: any) => {
    onSaveClick(values, actions);
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
      initialValues={getInitialValues()}
      onSubmit={handleSubmit}
      validateOnBlur={false}
      validateOnChange={false}
    >
      {/* @ts-ignore */}
      {(props: FormikProps<Values>) => (
        <Form noValidate>
          <VStack align="stretch" gap="24px">
            {/* Name */}
            <Field
              id="name"
              name="name"
              validate={(value: string) => validateField("Name", value)}
            >
              {({ field }: { field: any }) => (
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
                    />
                    <FormErrorMessage>{props.errors.name}</FormErrorMessage>
                  </VStack>
                  <CircleHelpIcon marginLeft="8px" visibility="hidden" />
                </FormControl>
              )}
            </Field>
            {/* Description */}
            <Field id="description" name="description">
              {({ field }: { field: any }) => (
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
                  />
                  <CircleHelpIcon marginLeft="8px" visibility="hidden" />
                </FormControl>
              )}
            </Field>
            {/* Connection Identifier */}
            <Field
              id="instance_key"
              name="instance_key"
              validate={validateConnectionIdentifier}
            >
              {({ field }: { field: any }) => (
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
                      isDisabled={connection?.key}
                      placeholder={`A a unique identifier for your new ${
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
                    <CircleHelpIcon
                      marginLeft="8px"
                      _hover={{ cursor: "pointer" }}
                    />
                  </Tooltip>
                </FormControl>
              )}
            </Field>
            {/* Dynamic connector secret fields */}
            {Object.entries(data.properties).map(([key, item]) =>
              getFormField(key, item)
            )}
            <ButtonGroup size="sm" spacing="8px" variant="outline">
              <Button
                colorScheme="gray.700"
                isDisabled={!connection?.key}
                isLoading={result.isLoading || result.isFetching}
                loadingText="Testing"
                onClick={handleTestConnectionClick}
                variant="outline"
              >
                Test connection
              </Button>
              <Button
                bg="primary.800"
                color="white"
                isLoading={isSubmitting}
                loadingText="Submitting"
                size="sm"
                variant="solid"
                type="submit"
                _active={{ bg: "primary.500" }}
                _disabled={{ opacity: "inherit" }}
                _hover={{ bg: "primary.400" }}
              >
                Save
              </Button>
            </ButtonGroup>
          </VStack>
        </Form>
      )}
    </Formik>
  );
};

export default ConnectorParametersForm;
