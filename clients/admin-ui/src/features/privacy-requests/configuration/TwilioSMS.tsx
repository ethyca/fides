import { Box, Button, Heading, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";

import { CustomTextInput } from "~/features/common/form/inputs";
import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import { messagingProviders } from "~/features/privacy-requests/constants";
import { useCreateMessagingConfigurationSecretsMutation } from "~/features/privacy-requests/privacy-requests.slice";

const TwilioSMSConfiguration = () => {
  const { successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const [createMessagingConfigurationSecrets] =
    useCreateMessagingConfigurationSecretsMutation();

  const handleTwilioTextConfigurationSecrets = async (value: {
    account_sid: string;
    auth_token: string;
    messaging_service_sid: string;
    phone: string;
  }) => {
    const result = await createMessagingConfigurationSecrets({
      details: {
        twilio_account_sid: value.account_sid,
        twilio_auth_token: value.auth_token,
        twilio_messaging_service_sid: value.messaging_service_sid,
        twilio_sender_phone_number: value.phone,
      },
      service_type: messagingProviders.twilio_text,
    });

    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      successAlert(`Twilio text secrets successfully updated.`);
    }
  };

  const initialValues = {
    account_sid: "",
    auth_token: "",
    messaging_service_sid: "",
    phone: "",
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
          enableReinitialize
        >
          {({ isSubmitting, handleReset }) => (
            <Form>
              <Stack mt={5} spacing={5}>
                <CustomTextInput
                  name="account_sid"
                  label="Account SID"
                  placeholder="Enter account SID"
                  isRequired
                />
                <CustomTextInput
                  name="auth_token"
                  label="Auth token"
                  placeholder="Enter auth token"
                  type="password"
                  isRequired
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
                  onClick={() => handleReset()}
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
