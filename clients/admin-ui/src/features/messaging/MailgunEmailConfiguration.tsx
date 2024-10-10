import { AntButton as Button, Box, Divider, Heading, HStack, Stack, Text } from "fidesui";
import { Form, Formik } from "formik";
import { useState } from "react";

import { CustomTextInput } from "~/features/common/form/inputs";
import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import MailgunIcon from "~/features/messaging/MailgunIcon";

import { messagingProviders } from "./constants";
import {
  useCreateMessagingConfigurationMutation,
  useCreateMessagingConfigurationSecretsMutation,
  useGetMessagingConfigurationDetailsQuery,
} from "./messaging.slice";
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
        <HStack>
          <MailgunIcon />
          <Text>Mailgun messaging configuration</Text>
        </HStack>
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
                <Button onClick={handleReset} className="mr-2">
                  Cancel
                </Button>
                <Button
                  htmlType="submit"
                  disabled={isSubmitting}
                  type="primary"
                  data-testid="save-btn"
                >
                  Save
                </Button>
              </Box>
            </Form>
          )}
        </Formik>
      </Stack>
      {(configurationStep === "apiKey" ||
        configurationStep === "testConnection") && (
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
                  <Stack mt={5} spacing={5}>
                    <CustomTextInput
                      name="api_key"
                      label="API key"
                      type="password"
                      isRequired
                    />
                  </Stack>
                  <Box mt={10}>
                    <Button onClick={handleReset} className="mr-2">
                      Cancel
                    </Button>
                    <Button
                      disabled={isSubmitting}
                      htmlType="submit"
                      type="primary"
                      data-testid="save-btn"
                    >
                      Save
                    </Button>
                  </Box>
                </Form>
              )}
            </Formik>
          </Stack>
        </>
      )}
      {configurationStep === "testConnection" && (
        <TestMessagingProviderConnectionButton
          serviceType={messagingProviders.mailgun}
        />
      )}
    </Box>
  );
};

export default MailgunEmailConfiguration;
