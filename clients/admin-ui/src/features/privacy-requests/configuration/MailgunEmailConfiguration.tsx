import { Box, Button, Divider, Heading, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useState } from "react";
import { CustomTextInput } from "~/features/common/form/inputs";

const MailgunEmailConfiguration = () => {
  const [configurationStep, setConfigurationStep] = useState("");

  const handleMailgunConfiguration = () => {
    // API CALL 1
    // if successful
    setConfigurationStep("2");
  };

  const handleMailgunAPIKeyConfiguration = () => {
    // API CALL 2
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
    name: "",
    domain: "",
  };

  const initialAPIKeyValue = {
    api_key: "",
  };

  const initialEmailValue = {
    email: "",
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
