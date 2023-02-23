import { Box, Button, Divider, Heading, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useState } from "react";

import { CustomTextInput } from "~/features/common/form/inputs";
import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import {
  useCreateMessagingConfigurationMutation,
  useCreateMessagingConfigurationSecretsMutation,
  useGetMessagingConfigurationDetailsQuery,
} from "~/features/privacy-requests/privacy-requests.slice";

const TwilioEmailConfiguration = () => {
  const [configurationStep, setConfigurationStep] = useState("");
  const { successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const { data: messagingDetails } = useGetMessagingConfigurationDetailsQuery({
    type: "TWILIO_EMAIL",
  });
  const [createMessagingConfiguration] =
    useCreateMessagingConfigurationMutation();
  const [createMessagingConfigurationSecrets] =
    useCreateMessagingConfigurationSecretsMutation();

  const handleTwilioEmailConfiguration = async (value: { email: string }) => {
    const result = await createMessagingConfiguration({
      service_type: "TWILIO_EMAIL",
      details: {
        twilio_email_from: value.email,
      },
    });

    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      successAlert(
        `Twilio email successfully updated. You can now enter your security key.`
      );
      setConfigurationStep("configureTwilioEmailSecrets");
    }
  };

  const handleTwilioEmailConfigurationSecrets = async (value: {
    api_key: string;
  }) => {
    const result = await createMessagingConfigurationSecrets({
      twilio_api_key: value.api_key,
    });

    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      successAlert(`Twilio email secrets successfully updated.`);
      setConfigurationStep("configureTwilioEmailSecrets");
    }
  };

  const initialValues = {
    email: messagingDetails?.details.twilio_email_from ?? "",
  };

  const initialAPIKeyValues = {
    api_key: messagingDetails?.key ?? "",
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
          {({ isSubmitting, resetForm }) => (
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
                <Button
                  onClick={() => resetForm()}
                  mr={2}
                  size="sm"
                  variant="outline"
                >
                  Cancel
                </Button>
                <Button
                  isDisabled={isSubmitting}
                  type="submit"
                  colorScheme="primary"
                  size="sm"
                  data-testid="save-btn"
                >
                  Save
                </Button>
              </Box>
            </Form>
          )}
        </Formik>
      </Stack>
      {configurationStep === "configureTwilioEmailSecrets" ? (
        <>
          <Divider />
          <Heading fontSize="md" fontWeight="semibold" mt={10}>
            Security key
          </Heading>
          <Stack>
            <Formik
              initialValues={initialAPIKeyValues}
              onSubmit={handleTwilioEmailConfigurationSecrets}
            >
              {({ isSubmitting, resetForm }) => (
                <Form>
                  <Stack mt={5} spacing={5}>
                    <CustomTextInput
                      name="api-key"
                      label="API key"
                      type="password"
                      isRequired
                    />
                  </Stack>
                  <Button
                    onClick={() => resetForm()}
                    mr={2}
                    size="sm"
                    variant="outline"
                  >
                    Cancel
                  </Button>
                  <Button
                    isDisabled={isSubmitting}
                    type="submit"
                    colorScheme="primary"
                    size="sm"
                    data-testid="save-btn"
                  >
                    Save
                  </Button>
                </Form>
              )}
            </Formik>
          </Stack>
        </>
      ) : null}
    </Box>
  );
};

export default TwilioEmailConfiguration;
