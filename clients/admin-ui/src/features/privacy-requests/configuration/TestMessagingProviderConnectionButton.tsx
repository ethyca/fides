import { Box, Button, Divider, Heading, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";

import { CustomTextInput } from "~/features/common/form/inputs";
import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import { messagingProviders } from "~/features/privacy-requests/constants";
import { useCreateTestConnectionMessageMutation } from "~/features/privacy-requests/privacy-requests.slice";

const TestMessagingProviderConnectionButton = ({ messagingDetails }: any) => {
  const { successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const [createTestConnectionMessage] =
    useCreateTestConnectionMessageMutation();

  const emailProvider =
    messagingDetails.service_type === messagingProviders.twilio_email ||
    messagingDetails.service_type === messagingProviders.mailgun;

  const SMSProvider =
    messagingDetails.service_type === messagingProviders.twilio_text;

  const initialValues = {
    email: "",
    phone: "",
  };

  const handleTestConnection = async (value: {
    email: string;
    phone: string;
  }) => {
    if (emailProvider) {
      const result = await createTestConnectionMessage({
        email: value.email,
      });

      if (isErrorResult(result)) {
        handleError(result.error);
      } else {
        successAlert(`Test message successfully sent.`);
      }
    }
    if (SMSProvider) {
      const result = await createTestConnectionMessage({
        phone_number: value.phone,
      });

      if (isErrorResult(result)) {
        handleError(result.error);
      } else {
        successAlert(`Test message successfully sent.`);
      }
    }
  };

  return (
    <>
      <Divider mt={10} />
      <Heading fontSize="md" fontWeight="semibold" mt={10} mb={5}>
        Test connection
      </Heading>
      <Stack>
        <Formik initialValues={initialValues} onSubmit={handleTestConnection}>
          {({ isSubmitting, resetForm }) => (
            <Form>
              {emailProvider ? (
                <CustomTextInput
                  name="email"
                  label="Email"
                  placeholder="youremail@domain.com"
                  isRequired
                />
              ) : null}
              {SMSProvider ? (
                <CustomTextInput
                  name="phone"
                  label="Phone"
                  placeholder="+10000000000"
                  isRequired
                />
              ) : null}
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
    </>
  );
};

export default TestMessagingProviderConnectionButton;
