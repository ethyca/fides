/* eslint-disable react/no-array-index-key */
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import {
  AntButton,
  Box,
  DeleteIcon,
  Flex,
  Heading,
  Spinner,
  Text,
  useToast,
} from "fidesui";
import { FieldArray, Form, Formik, FormikHelpers } from "formik";
import type { NextPage } from "next";
import * as Yup from "yup";

import { useAppSelector } from "~/app/hooks";
import DocsLink from "~/features/common/DocsLink";
import FormSection from "~/features/common/form/FormSection";
import { CustomTextInput, TextInput } from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
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
  const currentSettings = useAppSelector(selectCORSOrigins);
  const apiSettings = currentSettings.apiSet;
  const configSettings = currentSettings.configSet;
  const hasConfigSettings: boolean = !!(
    configSettings.cors_origins?.length || configSettings.cors_origin_regex
  );
  const applicationConfig = useAppSelector(selectApplicationConfig());
  const [putConfigSettingsTrigger, { isLoading: isLoadingPutMutation }] =
    usePutConfigurationSettingsMutation();

  const toast = useToast();

  const isValidURL = (value: string | undefined) => {
    if (
      !value ||
      !(value.startsWith("https://") || value.startsWith("http://"))
    ) {
      return false;
    }
    try {
      /* eslint-disable-next-line no-new */
      new URL(value);
    } catch (e) {
      return false;
    }
    return true;
  };

  const containsNoWildcard = (value: string | undefined) => {
    if (!value) {
      return false;
    }
    return !value.includes("*");
  };

  const containsNoPath = (value: string | undefined) => {
    if (!value) {
      return false;
    }
    try {
      const url = new URL(value);
      return url.pathname === "/" && !value.endsWith("/");
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
            (value) => isValidURL(value),
          )
          .test(
            "has-no-wildcard",
            ({ label }) =>
              `${label} cannot contain a wildcard (e.g. https://*.example.com)`,
            (value) => containsNoWildcard(value),
          )
          .test(
            "has-no-path",
            ({ label }) =>
              `${label} cannot contain a path (e.g. https://example.com/path)`,
            (value) => containsNoPath(value),
          )
          .label("Domain"),
      ),
  });

  const handleSubmit = async (
    values: FormValues,
    formikHelpers: FormikHelpers<FormValues>,
  ) => {
    const handleResult = (
      result:
        | { data: object }
        | { error: FetchBaseQueryError | SerializedError },
    ) => {
      toast.closeAll();
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          `An unexpected error occurred while saving domains. Please try again.`,
        );
        toast(errorToastParams(errorMsg));
      } else {
        toast(successToastParams("Domains saved successfully"));
        // Reset state such that isDirty will be checked again before next save
        formikHelpers.resetForm({ values });
      }
    };

    const payloadOrigins =
      values.cors_origins && values.cors_origins.length > 0
        ? values.cors_origins
        : undefined;

    // Ensure that we include the existing applicationConfig (for other API-set configs)
    const payload: PlusApplicationConfig = {
      ...applicationConfig,
      security: {
        cors_origins: payloadOrigins,
      },
    };

    const result = await putConfigSettingsTrigger(payload);

    handleResult(result);
  };

  return (
    <Layout title="Domains">
      <Box data-testid="management-domains">
        <Heading marginBottom={4} fontSize="2xl">
          Domains
        </Heading>
        <Box maxWidth="600px">
          <Text marginBottom={3} fontSize="sm">
            For Fides to work on your website(s), each of your domains must be
            listed below. You can add and remove domains at any time up to the
            quantity included in your license. For more information on managing
            domains{" "}
            <DocsLink href="https://fid.es/domain-configuration">
              read here
            </DocsLink>
            .
          </Text>
        </Box>

        <Box maxW="600px" paddingY={3}>
          <FormSection
            data-testid="api-set-domains-form"
            title="Organization domains"
            tooltip="Fides uses these domains to enforce cross-origin resource sharing (CORS), a browser-based security standard. Each domain must be a valid URL (e.g. https://example.com) without any wildcards '*' or paths '/blog'"
          >
            {isLoadingGetQuery || isLoadingPutMutation ? (
              <Flex justifyContent="center">
                <Spinner />
              </Flex>
            ) : (
              <Formik<FormValues>
                initialValues={apiSettings}
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
                                  placeholder="https://subdomain.example.com:9090"
                                />

                                <AntButton
                                  aria-label="delete-domain"
                                  className="z-[2] ml-8"
                                  icon={<DeleteIcon />}
                                  onClick={() => {
                                    arrayHelpers.remove(index);
                                  }}
                                >
                                  <DeleteIcon />
                                </AntButton>
                              </Flex>
                            ),
                          )}

                          <Flex justifyContent="center" mt={3}>
                            <AntButton
                              aria-label="add-domain"
                              className="w-full"
                              onClick={() => {
                                arrayHelpers.push("");
                              }}
                            >
                              Add domain
                            </AntButton>
                          </Flex>
                        </Flex>
                      )}
                    />

                    <Box mt={6}>
                      <AntButton
                        htmlType="submit"
                        type="primary"
                        disabled={isLoadingPutMutation || !dirty || !isValid}
                        loading={isLoadingPutMutation}
                        data-testid="save-btn"
                      >
                        Save
                      </AntButton>
                    </Box>
                  </Form>
                )}
              </Formik>
            )}
          </FormSection>
        </Box>
        <Box maxW="600px" marginY={3}>
          <FormSection
            data-testid="config-set-domains-form"
            title="Advanced settings"
            tooltip="These domains are configured by an administrator with access to Fides security settings and can support more advanced options such as wildcards and regex."
          >
            {isLoadingConfigSetQuery ? (
              <Flex justifyContent="center">
                <Spinner />
              </Flex>
            ) : (
              <Flex flexDir="column">
                {configSettings.cors_origins!.map((origin, index) => (
                  <TextInput
                    data-testid={`input-config_cors_origins[${index}]`}
                    key={index}
                    marginY={3}
                    value={origin}
                    isDisabled
                    isPassword={false}
                  />
                ))}
                {configSettings.cors_origin_regex ? (
                  <TextInput
                    data-testid="input-config_cors_origin_regex"
                    key="cors_origin_regex"
                    marginY={3}
                    value={configSettings.cors_origin_regex}
                    isDisabled
                    isPassword={false}
                  />
                ) : undefined}
                {!hasConfigSettings ? (
                  <Text fontSize="xs" color="gray.500">
                    No advanced domain settings configured.
                  </Text>
                ) : undefined}
              </Flex>
            )}
          </FormSection>
        </Box>
      </Box>
    </Layout>
  );
};
export default CORSConfigurationPage;
