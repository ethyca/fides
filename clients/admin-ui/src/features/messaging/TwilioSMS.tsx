import { AntButton as Button, Box, Heading, Stack } from "fidesui";
import { Form, Formik } from "formik";
import { useState } from "react";

import { CustomTextInput } from "~/features/common/form/inputs";
import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import { messagingProviders } from "~/features/privacy-requests/constants";

import TestMessagingProviderConnectionButton from "../privacy-requests/configuration/TestMessagingProviderConnectionButton";
import {
  useCreateMessagingConfigurationSecretsMutation,
  useGetMessagingConfigurationDetailsQuery,
} from "./messaging.slice";

const TwilioSMSConfiguration = () => {
  const { successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const [configurationStep, setConfigurationStep] = useState("");
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
      setConfigurationStep("testConnection");
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
      {configurationStep === "testConnection" ? (
        <TestMessagingProviderConnectionButton
          messagingDetails={
            messagingDetails || { service_type: messagingProviders.twilio_text }
          }
        />
      ) : null}
    </Box>
  );
};

export default TwilioSMSConfiguration;
