import {
  Button,
  ButtonGroup,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Input,
  Textarea,
  Tooltip,
  useToast,
  VStack,
} from "@fidesui/react";
import { isErrorWithDetail, isErrorWithDetailArray } from "common/helpers";
import { CircleHelpIcon } from "common/Icon";
import { capitalize } from "common/utils";
import {
  ConnectionOption,
  ConnectionTypeSecretSchemaReponse,
} from "connection-type/types";
import { SaasType } from "datastore-connections/constants";
import {
  useCreateSassConnectionConfigMutation,
  useLazyGetDatastoreConnectionStatusQuery,
} from "datastore-connections/datastore-connection.slice";
import { SassConnectionConfigRequest } from "datastore-connections/types";
import { Field, Form, Formik } from "formik";
import React, { useEffect, useRef, useState } from "react";

import { SassConnectorTemplate } from "../types";

const defaultValues: SassConnectorTemplate = {
  description: "",
  instance_key: "",
  name: "",
};

type ConnectorParametersProps = {
  connectionOption: ConnectionOption;
  data: ConnectionTypeSecretSchemaReponse;
  onTestConnectionClick: (value: any) => void;
};

export const ConnectorParameters: React.FC<ConnectorParametersProps> = ({
  connectionOption,
  data,
  onTestConnectionClick,
}) => {
  const mounted = useRef(false);
  const toast = useToast();
  const [connectionKey, setConnectionKey] = useState("");

  const [createSassConnectionConfig] = useCreateSassConnectionConfigMutation();
  const [trigger, result] = useLazyGetDatastoreConnectionStatusQuery();

  const validateField = (label: string, value: string) => {
    let error;
    if (!value) {
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

  const getFormField = (key: string, item: { title: string }): JSX.Element => (
    <Field
      id={key}
      name={key}
      key={key}
      validate={
        data.required.includes(key)
          ? (value: string) => validateField(item.title, value)
          : false
      }
    >
      {({ field, form }: { field: any; form: any }) => (
        <FormControl
          display="flex"
          isRequired={data.required.includes(key)}
          isInvalid={form.errors[key] && form.touched[key]}
        >
          {getFormLabel(key, item.title)}
          <VStack align="flex-start" w="inherit">
            <Input {...field} color="gray.700" size="sm" />
            <FormErrorMessage>{form.errors[key]}</FormErrorMessage>
          </VStack>
          <CircleHelpIcon marginLeft="8px" visibility="hidden" />
        </FormControl>
      )}
    </Field>
  );

  const getInitialValues = () => {
    Object.entries(data.properties).forEach((key) => {
      defaultValues[key[0]] = "";
    });
    return defaultValues;
  };

  const handleError = (error: any) => {
    let errorMsg = "An unexpected error occurred. Please try again.";
    if (isErrorWithDetail(error)) {
      errorMsg = error.data.detail;
    } else if (isErrorWithDetailArray(error)) {
      errorMsg = error.data.detail[0].msg;
    }
    toast({
      status: "error",
      description: errorMsg,
    });
  };

  const handleSubmit = async (values: any, actions: any) => {
    try {
      const params: SassConnectionConfigRequest = {
        description: values.description,
        instance_key: (values.instance_key as string)
          .toLowerCase()
          .replace(/ /g, "_"),
        name: values.name,
        saas_connector_type: connectionOption.identifier as SaasType,
        secrets: {},
      };
      Object.entries(data.properties).forEach((key) => {
        params.secrets[key[0]] = values[key[0]];
      });
      const payload = await createSassConnectionConfig(params).unwrap();
      setConnectionKey(payload.connection.key);
      toast({
        status: "success",
        description: "Connector successfully added!",
      });
    } catch (error) {
      handleError(error);
    } finally {
      actions.setSubmitting(false);
    }
  };

  const handleTestConnectionClick = async () => {
    try {
      await trigger(connectionKey).unwrap();
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
    >
      {(props) => (
        <Form noValidate>
          <VStack align="stretch" gap="24px">
            {/* Name */}
            <Field
              id="name"
              name="name"
              validate={(value: string) => validateField("Name", value)}
            >
              {({ field, form }: { field: any; form: any }) => (
                <FormControl
                  display="flex"
                  isRequired
                  isInvalid={form.errors.name && form.touched.name}
                >
                  {getFormLabel("name", "Name")}
                  <VStack align="flex-start" w="inherit">
                    <Input
                      {...field}
                      autoFocus
                      color="gray.700"
                      placeholder={`Enter a friendly name for your new ${capitalize(
                        connectionOption.identifier
                      )} connection`}
                      size="sm"
                    />
                    <FormErrorMessage>{form.errors.name}</FormErrorMessage>
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
                    placeholder={`Enter a description for your new ${capitalize(
                      connectionOption.identifier
                    )} connection`}
                    resize="none"
                    size="sm"
                  />
                  <CircleHelpIcon marginLeft="8px" visibility="hidden" />
                </FormControl>
              )}
            </Field>
            {/* Connection Identifier */}
            <Field id="instance_key" name="instance_key">
              {({ field }: { field: any }) => (
                <FormControl display="flex" isRequired>
                  {getFormLabel("instance_key", "Connection Identifier")}
                  <Input
                    {...field}
                    color="gray.700"
                    placeholder={`A a unique identifier for your new ${capitalize(
                      connectionOption.identifier
                    )} connection`}
                    size="sm"
                  />
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
                isDisabled={!connectionKey}
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
                isLoading={props.isSubmitting}
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
