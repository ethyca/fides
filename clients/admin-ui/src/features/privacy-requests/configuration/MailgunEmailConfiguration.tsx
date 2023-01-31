import { Box, Button, Divider, Heading, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useState } from "react";
import { CustomTextInput } from "~/features/common/form/inputs";

const MailgunEmailConfiguration = ({ messagingDetails }) => {
  const [configurationStep, setConfigurationStep] = useState("");

  console.log("existing details", messagingDetails);

  const handleMailgunConfiguration = () => {
    // API CALL 1
    // PATCH /api/v1/messaging/config/{config_key}

    // if successful - get the secret if it's there and then go to next step
    // GET /api/v1/messaging/config/{config_key}/secret
    setConfigurationStep("2");
  };

  const handleMailgunAPIKeyConfiguration = () => {
    // API CALL 2
    // PUT /api/v1messaging/config/{config_key}/secret

    // if successful
    setConfigurationStep("3");
  };

  const handleTestConnection = () => {
    // API CALL 3 - test connection
    console.log("test 3");
  };

  const MAILGUN_MESSAGING_CONFIG_FORM_ID = "mailgun-messaging-config-form-id";
  const MAILGUN_MESSAGING_CONFIG_API_KEY_FORM_ID =
    "mailgun-messaging-config-api-key-form-id";
  const MAILGUN_MESSAGING_CONFIG_EMAIL_FORM_ID =
    "mailgun-messaging-config-email-form-id";

  const initialValues = {
    name: messagingDetails.name ?? "",
    domain: messagingDetails.domain ?? "",
  };

  const initialAPIKeyValue = {
    api_key: messagingDetails.api_key ?? "",
  };

  const initialEmailValue = {
    email: messagingDetails.email ?? "",
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
        >
          {({ isSubmitting, resetForm }) => (
            <Form id={MAILGUN_MESSAGING_CONFIG_FORM_ID}>
              <CustomTextInput
                name="name"
                label="Name"
                placeholder="Enter name"
              />
              <CustomTextInput
                name="domain"
                label="Domain"
                placeholder="Enter domain"
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
                form={MAILGUN_MESSAGING_CONFIG_FORM_ID}
                isLoading={false}
              >
                Save
              </Button>
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
      ) : null}
    </Box>
  );
};

export default MailgunEmailConfiguration;
