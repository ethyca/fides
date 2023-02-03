import { Box, Button, Heading, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";

import { CustomTextInput } from "~/features/common/form/inputs";
import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import {
  useCreateMessagingConfigurationSecretsMutation,
  useGetMessagingConfigurationDetailsQuery,
} from "~/features/privacy-requests/privacy-requests.slice";

const TwilioSMSConfiguration = () => {
  const { successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const { data: messagingDetails } = useGetMessagingConfigurationDetailsQuery({
    type: "twilio_text",
  });
  const [createMessagingConfigurationSecrets] =
    useCreateMessagingConfigurationSecretsMutation();

  const handleTwilioTextConfigurationSecrets = async (value: {
    account_sid: string;
    auth_token: string;
    messaging_service_sid: string;
    phone: string;
  }) => {
    const result = await createMessagingConfigurationSecrets({
      twilio_account_sid: value.account_sid,
      twilio_auth_token: value.auth_token,
      twilio_messaging_service_sid: value.messaging_service_sid,
      twilio_sender_phone_number: value.phone,
    });

    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      successAlert(`Twilio text secrets successfully updated.`);
    }
  };

  const initialValues = {
    account_sid: messagingDetails.account_sid ?? "",
    auth_token: messagingDetails.auth_token ?? "",
    messaging_service_sid: messagingDetails.messaging_service_sid ?? "",
    phone: messagingDetails.phone ?? "",
  };

  return (
    <Box>
      <Heading fontSize="md" fontWeight="semibold" mt={10}>
        Twilio SMS messaging configuration
      </Heading>
      <Stack>
        <Formik
          initialValues={initialValues}
          onSubmit={handleTwilioTextConfigurationSecrets}
        >
          {({ isSubmitting, resetForm }) => (
            <Form>
              <Stack mt={5} spacing={5}>
                <CustomTextInput
                  name="account_sid"
                  label="Account SID"
                  placeholder="Enter account SID"
                />
                <CustomTextInput
                  name="auth_token"
                  label="Auth token"
                  placeholder="Enter auth token"
                  type="password"
                />
                <CustomTextInput
                  name="messaging_service_sid"
                  label="Messaging Service SID"
                  placeholder="Enter messaging service SID"
                />
                <CustomTextInput
                  name="phone"
                  label="Phone Number"
                  placeholder="Enter phone number"
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
    </Box>
  );
};

export default TwilioSMSConfiguration;
