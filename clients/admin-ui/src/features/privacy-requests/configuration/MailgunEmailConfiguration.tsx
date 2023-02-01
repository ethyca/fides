import { Box, Button, Divider, Heading, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useState } from "react";
import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";

import { CustomTextInput } from "~/features/common/form/inputs";
import {
  useGetMessagingConfigurationDetailsQuery,
  useCreateMessagingConfigurationMutation,
  useCreateMessagingConfigurationSecretsMutation,
} from "~/features/privacy-requests/privacy-requests.slice";

const MailgunEmailConfiguration = () => {
  const { errorAlert, successAlert } = useAlert();
  const [configurationStep, setConfigurationStep] = useState("");
  const { data: messagingDetails } = useGetMessagingConfigurationDetailsQuery({
    type: "mailgun",
  });
  const [createMessagingConfiguration] =
    useCreateMessagingConfigurationMutation();
  const [createMessagingConfigurationSecrets] =
    useCreateMessagingConfigurationSecretsMutation();

  const handleMailgunConfiguration = async (value) => {
    const payload = await createMessagingConfiguration({
      type: "mailgun",
      details: {
        is_eu_domain: "false",
        domain: value.domain,
      },
    });

    if ("error" in payload) {
      errorAlert(
        getErrorMessage(payload.error),
        `Configuring storage type has failed to save due to the following:`
      );
    } else {
      successAlert(`Configure storage type saved successfully.`);
      setConfigurationStep("2");
    }
  };

  const handleMailgunAPIKeyConfiguration = async (value) => {
    const payload = await createMessagingConfigurationSecrets({
      mailgun_api_key: value.api_key,
    });

    if ("error" in payload) {
      errorAlert(
        getErrorMessage(payload.error),
        `Configuring storage type has failed to save due to the following:`
      );
    } else {
      successAlert(`Configure storage type saved successfully.`);
      setConfigurationStep("3");
    }
  };

  // const handleTestConnection = () => {
  //   setConfigurationStep("4");
  // };

  const MAILGUN_MESSAGING_CONFIG_FORM_ID = "mailgun-messaging-config-form-id";
  const MAILGUN_MESSAGING_CONFIG_API_KEY_FORM_ID =
    "mailgun-messaging-config-api-key-form-id";
  // const MAILGUN_MESSAGING_CONFIG_EMAIL_FORM_ID =
  //   "mailgun-messaging-config-email-form-id";

  const initialValues = {
    domain: messagingDetails.domain ?? "",
  };

  const initialAPIKeyValue = {
    api_key: messagingDetails.api_key ?? "",
  };

  // const initialEmailValue = {
  //   email: email ?? "",
  // };

  return (
    <Box>
      <Heading fontSize="md" fontWeight="semibold" mt={10}>
        Mailgun messaging configuration
      </Heading>
      <Stack>
        <Formik
          initialValues={initialValues}
          onSubmit={handleMailgunConfiguration}
        >
          {({ isSubmitting, resetForm }) => (
            <Form id={MAILGUN_MESSAGING_CONFIG_FORM_ID}>
              <CustomTextInput
                name="domain"
                label="Domain"
                placeholder="Enter domain"
              />
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
                  form={MAILGUN_MESSAGING_CONFIG_FORM_ID}
                  isLoading={false}
                >
                  Save
                </Button>
              </Box>
            </Form>
          )}
        </Formik>
      </Stack>
      {configurationStep === "2" || configurationStep === "3" ? (
        <>
          <Divider />
          <Heading fontSize="md" fontWeight="semibold" mt={10}>
            Security key
          </Heading>
          <Stack>
            <Formik
              initialValues={initialAPIKeyValue}
              onSubmit={handleMailgunAPIKeyConfiguration}
            >
              {({ isSubmitting, resetForm }) => (
                <Form id={MAILGUN_MESSAGING_CONFIG_API_KEY_FORM_ID}>
                  <CustomTextInput
                    name="api-key"
                    label="API key"
                    placeholder="Optional"
                  />
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
                    form={MAILGUN_MESSAGING_CONFIG_API_KEY_FORM_ID}
                    isLoading={false}
                  >
                    Save
                  </Button>
                </Form>
              )}
            </Formik>
          </Stack>
        </>
      ) : null}
      {/* This will be added in the next sprint
      {configurationStep === "3" ? (
        <>
          <Divider />
          <Heading fontSize="md" fontWeight="semibold" mt={10}>
            Test connection
          </Heading>
          <Stack>
            <Formik
              initialValues={initialEmailValue}
              onSubmit={handleTestConnection}
            >
              {({ isSubmitting, resetForm }) => (
                <Form id={MAILGUN_MESSAGING_CONFIG_EMAIL_FORM_ID}>
                  <CustomTextInput
                    name="email"
                    label="Email"
                    placeholder="youremail@domain.com"
                  />
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
                    form={MAILGUN_MESSAGING_CONFIG_EMAIL_FORM_ID}
                    isLoading={false}
                  >
                    Save
                  </Button>
                </Form>
              )}
            </Formik>
      </Stack>
        </>
      ) : null} */}
    </Box>
  );
};

export default MailgunEmailConfiguration;
