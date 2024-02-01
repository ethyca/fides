/* eslint-disable react/no-array-index-key */
import { AddIcon } from "@chakra-ui/icons";
import {
  Box,
  Button,
  DeleteIcon,
  Flex,
  Heading,
  IconButton,
  Spinner,
  Text,
  useToast,
} from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import { FieldArray, Form, Formik, FormikHelpers } from "formik";
import type { NextPage } from "next";
import * as Yup from "yup";

import { useAppSelector } from "~/app/hooks";
import DocsLink from "~/features/common/DocsLink";
import FormSection from "~/features/common/form/FormSection";
import { CustomTextInput, TextInput } from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  CORSOrigins,
  selectApplicationConfig,
  selectCORSOrigins,
  useGetConfigurationSettingsQuery,
  usePutConfigurationSettingsMutation,
} from "~/features/privacy-requests/privacy-requests.slice";
import { PlusApplicationConfig } from "~/types/api";

type FormValues = CORSOrigins;

const CORSConfigurationPage: NextPage = () => {
  const { isLoading: isLoadingGetQuery } = useGetConfigurationSettingsQuery({
    api_set: true,
  });
  const { isLoading: isLoadingConfigSetQuery } =
    useGetConfigurationSettingsQuery({
      api_set: false,
    });
  const corsOriginSettings = useAppSelector(selectCORSOrigins);
  const apiSetCorsOrigins = corsOriginSettings.apiSet;
  const configSetCorsOrigins = corsOriginSettings.configSet;
  const applicationConfig = useAppSelector(selectApplicationConfig());
  const [putConfigSettingsTrigger, { isLoading: isLoadingPutMutation }] =
    usePutConfigurationSettingsMutation();

  const toast = useToast();

  const isValidURL = (value: string | undefined) => {
    if (!value) {
      return false;
    }
    try {
      new URL(value);
    } catch (e) {
      return false;
    }
    return true;
  };

  const urlContainsNoPath = (value: string | undefined) => {
    if (!value) {
      return false;
    }
    try {
      const url = new URL(value);
      return url.pathname === "/" && !value.endsWith("/")
    } catch (e) {
      return false;
    }
  };

  const ValidationSchema = Yup.object().shape({
    cors_origins: Yup.array()
      .nullable()
      .of(
        Yup.string()
          .required()
          .trim()
          .test(
            "is-valid-url",
            ({ label }) =>
              `${label} must be a valid URL (e.g. https://example.com)`,
            (value) => isValidURL(value)
          )
          .test(
            "has-no-path",
            ({ label }) =>
              `${label} cannot contain a path (e.g. https://example.com/path)`,
            (value) => urlContainsNoPath(value)
          )
          .label("Domain")
      ),
  });

  const handleSubmit = async (
    values: FormValues,
    formikHelpers: FormikHelpers<FormValues>
  ) => {
    const handleResult = (
      result: { data: {} } | { error: FetchBaseQueryError | SerializedError }
    ) => {
      toast.closeAll();
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          `An unexpected error occurred while saving CORS domains. Please try again.`
        );
        toast(errorToastParams(errorMsg));
      } else {
        toast(successToastParams("CORS domains saved successfully"));
        // Reset state such that isDirty will be checked again before next save
        formikHelpers.resetForm({ values });
      }
    };

    const payloadOrigins =
      values.cors_origins && values.cors_origins.length > 0
        ? values.cors_origins
        : undefined;

    // Ensure that we include the existing applicationConfig (for other API-set configs)
    // TODO: is this necessary?
    const payload: PlusApplicationConfig = {
      ...applicationConfig,
      security: {
        cors_origins: payloadOrigins,
      },
    };

    console.log("putConfigSettings", payload);
    const result = await putConfigSettingsTrigger(payload);

    handleResult(result);
  };

  return (
    <Layout title="Manage domains">
      <Box data-testid="cors-configuration">
        <Heading marginBottom={4} fontSize="2xl">
          Manage domains
        </Heading>
        <Box maxWidth="600px">
          <Text marginBottom={2} fontSize="md">
            Manage domains for your organization
          </Text>
          <Text mb={10} fontSize="sm">
            You must add domains associated with your organization to Fides to
            ensure features such as consent function correctly. For more
            information on managing domains on Fides, click here{" "}
            <DocsLink href="https://fid.es/cors-configuration">
              docs.ethyca.com
            </DocsLink>
            .
          </Text>
        </Box>

        <Box maxW="600px" marginY={3}>
          <FormSection title="CORS domains">
            {isLoadingGetQuery || isLoadingPutMutation ? (
              <Flex justifyContent="center">
                <Spinner />
              </Flex>
            ) : (
              <Formik<FormValues>
                initialValues={apiSetCorsOrigins}
                enableReinitialize
                onSubmit={handleSubmit}
                validationSchema={ValidationSchema}
                validateOnChange
              >
                {({ dirty, values, isValid }) => (
                  <Form>
                    <FieldArray
                      name="cors_origins"
                      render={(arrayHelpers) => (
                        <Flex flexDir="column">
                          {values.cors_origins!.map(
                            (_: string, index: number) => (
                              <Flex flexDir="row" key={index} my={3}>
                                <CustomTextInput
                                  variant="stacked"
                                  name={`cors_origins[${index}]`}
                                />

                                <IconButton
                                  ml={8}
                                  aria-label="delete-cors-domain"
                                  variant="outline"
                                  zIndex={2}
                                  size="sm"
                                  onClick={() => {
                                    arrayHelpers.remove(index);
                                  }}
                                >
                                  <DeleteIcon />
                                </IconButton>
                              </Flex>
                            )
                          )}

                          <Flex justifyContent="center" mt={3}>
                            <Button
                              aria-label="add-cors-domain"
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                arrayHelpers.push("");
                              }}
                              rightIcon={<AddIcon />}
                            >
                              Add CORS domain
                            </Button>
                          </Flex>
                        </Flex>
                      )}
                    />

                    <Box mt={6}>
                      <Button
                        type="submit"
                        variant="primary"
                        size="sm"
                        isDisabled={isLoadingPutMutation || !dirty || !isValid}
                        isLoading={isLoadingPutMutation}
                        data-testid="save-btn"
                      >
                        Save
                      </Button>
                    </Box>
                  </Form>
                )}
              </Formik>
            )}
          </FormSection>
        </Box>
        <Box maxW="600px" marginY={3}>
          <FormSection
            // TODO: move this into a tooltip prop
            title={
              <Flex flexDir="row" alignItems="center" gap={1}>
                <Flex>Security Domains</Flex>
                <QuestionTooltip label="These domains are configured in your Fides security settings by an administrator" />
              </Flex>
            }
          >
            {isLoadingConfigSetQuery ? (
              <Flex justifyContent="center">
                <Spinner />
              </Flex>
            ) : (
              <Flex flexDir="column">
                {configSetCorsOrigins.cors_origins!.map((origin, index) => (
                  <TextInput
                    key={index}
                    marginY={3}
                    value={origin}
                    isDisabled={true}
                    isPassword={false}
                    name={`config_set_cors_origins[${index}]`}
                  />
                ))}
              </Flex>
            )}
          </FormSection>
        </Box>
      </Box>
    </Layout>
  );
};
export default CORSConfigurationPage;
