import { Box, Button, Divider, Heading, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useState } from "react";

import { CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import {
  useCreateMessagingConfigurationMutation,
  useCreateMessagingConfigurationSecretsMutation,
  useGetMessagingConfigurationDetailsQuery,
} from "~/features/privacy-requests/privacy-requests.slice";

const TwilioEmailConfiguration = () => {
  const [configurationStep, setConfigurationStep] = useState("");
  const { errorAlert, successAlert } = useAlert();
  const { data: messagingDetails } = useGetMessagingConfigurationDetailsQuery({
    type: "twilio_email",
  });
  const [createMessagingConfiguration] =
    useCreateMessagingConfigurationMutation();
  const [createMessagingConfigurationSecrets] =
    useCreateMessagingConfigurationSecretsMutation();

  const handleTwilioEmailConfiguration = async (value: { email: string }) => {
    const payload = await createMessagingConfiguration({
      type: "twilio_email",
      details: {
        twilio_email_from: value.email,
      },
    });

    if ("error" in payload) {
      errorAlert(
        getErrorMessage(payload.error),
        `Configuring messaging provider has failed to save due to the following:`
      );
    } else {
      successAlert(`Configure messaging provider saved successfully.`);
      setConfigurationStep("2");
    }
  };

  const handleTwilioEmailConfigurationSecrets = async (value: {
    api_key: string;
  }) => {
    const payload = await createMessagingConfigurationSecrets({
      twilio_api_key: value.api_key,
    });

    if ("error" in payload) {
      errorAlert(
        getErrorMessage(payload.error),
        `Configuring messaging provider secrets has failed to save due to the following:`
      );
    } else {
      successAlert(`Configure messaging provider secrets saved successfully.`);
    }
  };

  const initialValues = {
    email: messagingDetails.email ?? "",
  };

  const initialAPIKeyValues = {
    api_key: messagingDetails.api_key ?? "",
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
        >
          {({ isSubmitting, resetForm }) => (
            <Form>
              <Stack mt={5} spacing={5}>
                <CustomTextInput
                  name="email"
                  label="Email"
                  placeholder="Enter email"
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
                  disabled={isSubmitting}
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
      {configurationStep === "2" ? (
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
                    disabled={isSubmitting}
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
