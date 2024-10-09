import { AntButton as Button, Box, Divider, Heading, Stack } from "fidesui";
import { Form, Formik } from "formik";
import { useState } from "react";

import { CustomTextInput } from "~/features/common/form/inputs";
import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import { messagingProviders } from "~/features/privacy-requests/constants";

import TestMessagingProviderConnectionButton from "../privacy-requests/configuration/TestMessagingProviderConnectionButton";
import {
  useCreateMessagingConfigurationMutation,
  useCreateMessagingConfigurationSecretsMutation,
  useGetMessagingConfigurationDetailsQuery,
} from "./messaging.slice";

const TwilioEmailConfiguration = () => {
  const [configurationStep, setConfigurationStep] = useState("");
  const { successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const { data: messagingDetails } = useGetMessagingConfigurationDetailsQuery({
    type: messagingProviders.twilio_email,
  });
  const [createMessagingConfiguration] =
    useCreateMessagingConfigurationMutation();
  const [createMessagingConfigurationSecrets] =
    useCreateMessagingConfigurationSecretsMutation();

  const handleTwilioEmailConfiguration = async (value: { email: string }) => {
    const result = await createMessagingConfiguration({
      service_type: messagingProviders.twilio_email,
      details: {
        twilio_email_from: value.email,
      },
    });

    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      successAlert(
        `Twilio email successfully updated. You can now enter your security key.`,
      );
      setConfigurationStep("configureTwilioEmailSecrets");
    }
  };

  const handleTwilioEmailConfigurationSecrets = async (value: {
    api_key: string;
  }) => {
    const result = await createMessagingConfigurationSecrets({
      details: {
        twilio_api_key: value.api_key,
      },
      service_type: messagingProviders.twilio_email,
    });

    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      successAlert(`Twilio email secrets successfully updated.`);
      setConfigurationStep("testConnection");
    }
  };

  const initialValues = {
    email: messagingDetails?.details.twilio_email_from ?? "",
  };

  const initialAPIKeyValues = {
    api_key: "",
  };

  return (
    <Box>
      <Heading fontSize="md" fontWeight="semibold" mt={10}>
        Twilio Email messaging configuration
      </Heading>
      <Stack>
        <Formik
          initialValues={initialValues}
          onSubmit={handleTwilioEmailConfiguration}
          enableReinitialize
        >
          {({ isSubmitting, handleReset }) => (
            <Form>
              <Stack mt={5} spacing={5}>
                <CustomTextInput
                  name="email"
                  label="Email"
                  placeholder="Enter email"
                  isRequired
                />
              </Stack>
              <Box mt={10}>
                <Button onClick={() => handleReset()} className="mr-2">
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
      {configurationStep === "configureTwilioEmailSecrets" ||
      configurationStep === "testConnection" ? (
        <>
          <Divider mt={10} />
          <Heading fontSize="md" fontWeight="semibold" mt={10}>
            Security key
          </Heading>
          <Stack>
            <Formik
              initialValues={initialAPIKeyValues}
              onSubmit={handleTwilioEmailConfigurationSecrets}
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
                    <Button onClick={() => handleReset()} className="mr-2">
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
      ) : null}
      {configurationStep === "testConnection" ? (
        <TestMessagingProviderConnectionButton
          messagingDetails={
            messagingDetails || {
              service_type: messagingProviders.twilio_email,
            }
          }
        />
      ) : null}
    </Box>
  );
};

export default TwilioEmailConfiguration;
