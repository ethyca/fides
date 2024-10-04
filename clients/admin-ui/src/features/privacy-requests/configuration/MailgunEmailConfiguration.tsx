import { AntButton, Box, Divider, Heading, Stack } from "fidesui";
import { Form, Formik } from "formik";
import { useState } from "react";

import { CustomTextInput } from "~/features/common/form/inputs";
import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import { messagingProviders } from "~/features/privacy-requests/constants";
import {
  useCreateMessagingConfigurationMutation,
  useCreateMessagingConfigurationSecretsMutation,
  useGetMessagingConfigurationDetailsQuery,
} from "~/features/privacy-requests/privacy-requests.slice";

import TestMessagingProviderConnectionButton from "./TestMessagingProviderConnectionButton";

type ConnectionStep = "" | "apiKey" | "testConnection";

const MailgunEmailConfiguration = () => {
  const { successAlert } = useAlert();
  const [configurationStep, setConfigurationStep] =
    useState<ConnectionStep>("");
  const { handleError } = useAPIHelper();
  const { data: messagingDetails } = useGetMessagingConfigurationDetailsQuery({
    type: messagingProviders.mailgun,
  });
  const [createMessagingConfiguration] =
    useCreateMessagingConfigurationMutation();
  const [createMessagingConfigurationSecrets] =
    useCreateMessagingConfigurationSecretsMutation();

  const handleMailgunConfiguration = async (value: { domain: string }) => {
    const result = await createMessagingConfiguration({
      service_type: messagingProviders.mailgun,
      details: {
        is_eu_domain: "false",
        domain: value.domain,
      },
    });

    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      successAlert(
        `Mailgun email successfully updated. You can now enter your security key.`,
      );
      setConfigurationStep("apiKey");
    }
  };

  const handleMailgunAPIKeyConfiguration = async (value: {
    api_key: string;
  }) => {
    const result = await createMessagingConfigurationSecrets({
      details: {
        mailgun_api_key: value.api_key,
      },
      service_type: messagingProviders.mailgun,
    });

    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      successAlert(`Mailgun security key successfully updated.`);
      setConfigurationStep("testConnection");
    }
  };

  const initialValues = {
    domain: messagingDetails?.details.domain ?? "",
  };

  const initialAPIKeyValue = {
    api_key: "",
  };

  return (
    <Box>
      <Heading fontSize="md" fontWeight="semibold" mt={10}>
        Mailgun messaging configuration
      </Heading>
      <Stack>
        <Formik
          initialValues={initialValues}
          onSubmit={handleMailgunConfiguration}
          enableReinitialize
        >
          {({ isSubmitting, handleReset }) => (
            <Form>
              <Stack mt={5} spacing={5}>
                <CustomTextInput
                  name="domain"
                  label="Domain"
                  placeholder="Enter domain"
                  data-testid="option-twilio-domain"
                  isRequired
                />
              </Stack>
              <Box mt={10}>
                <AntButton onClick={handleReset} className="mr-2">
                  Cancel
                </AntButton>
                <AntButton
                  htmlType="submit"
                  disabled={isSubmitting}
                  type="primary"
                  data-testid="save-btn"
                >
                  Save
                </AntButton>
              </Box>
            </Form>
          )}
        </Formik>
      </Stack>
      {configurationStep === "apiKey" ||
      configurationStep === "testConnection" ? (
        <>
          <Divider mt={10} />
          <Heading fontSize="md" fontWeight="semibold" mt={10}>
            Security key
          </Heading>
          <Stack>
            <Formik
              initialValues={initialAPIKeyValue}
              onSubmit={handleMailgunAPIKeyConfiguration}
            >
              {({ isSubmitting, handleReset }) => (
                <Form>
                  <CustomTextInput
                    name="api_key"
                    label="API key"
                    type="password"
                    isRequired
                  />
                  <Box mt={10}>
                    <AntButton onClick={handleReset} className="mr-2">
                      Cancel
                    </AntButton>
                    <AntButton
                      disabled={isSubmitting}
                      htmlType="submit"
                      type="primary"
                      data-testid="save-btn"
                    >
                      Save
                    </AntButton>
                  </Box>
                </Form>
              )}
            </Formik>
          </Stack>
        </>
      ) : null}
      {configurationStep === "testConnection" ? (
        <TestMessagingProviderConnectionButton
          messagingDetails={
            messagingDetails || { service_type: messagingProviders.mailgun }
          }
        />
      ) : null}
    </Box>
  );
};

export default MailgunEmailConfiguration;
