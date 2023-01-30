import { Box, Button, Heading, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";
import { CustomTextInput } from "~/features/common/form/inputs";

const MailgunEmailConfiguration = () => {
  const handleMailgunConfiguration = () => {
    // API CALL 1
    console.log("test");
  };

  // API CALL 2

  // API CALL 3

  const MAILGUN_MESSAGING_CONFIG_FORM_ID = "mailgun-messaging-config-form-id";

  const initialValues = {
    name: "",
    domain: "",
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
    </Box>
  );
};

export default MailgunEmailConfiguration;
