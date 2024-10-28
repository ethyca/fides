import {
  AntButton as Button,
  Box,
  Heading,
  HStack,
  Stack,
  Text,
} from "fidesui";
import { Form, Formik } from "formik";
import { useState } from "react";

import { CustomTextInput } from "~/features/common/form/inputs";
import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import TwilioIcon from "~/features/messaging/TwilioIcon";

import { messagingProviders } from "./constants";
import {
  useCreateMessagingConfigurationMutation,
  useGetMessagingConfigurationDetailsQuery,
} from "./messaging.slice";
import TestMessagingProviderConnectionButton from "./TestMessagingProviderConnectionButton";

const TwilioEmailConfiguration = () => {
  const [configurationStep, setConfigurationStep] = useState("");
  const { successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const { data: messagingDetails } = useGetMessagingConfigurationDetailsQuery({
    type: messagingProviders.twilio_email,
  });
  const [createMessagingConfiguration] =
    useCreateMessagingConfigurationMutation();

  const handleTwilioEmailConfiguration = async (value: {
    email: string;
    api_key: string;
  }) => {
    const result = await createMessagingConfiguration({
      service_type: messagingProviders.twilio_email,
      details: {
        twilio_email_from: value.email,
      },
      secrets: {
        api_key: value.api_key,
      },
    });

    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      successAlert(`Twilio email successfully updated.`);
      setConfigurationStep("testConnection");
    }
  };

  const initialValues = {
    email: messagingDetails?.details.twilio_email_from ?? "",
    api_key: "",
  };

  return (
    <Box>
      <Heading fontSize="md" fontWeight="semibold" mt={10}>
        <HStack>
          <TwilioIcon />
          <Text>Twilio Email messaging configuration</Text>
        </HStack>
      </Heading>
      <Stack>
        <Formik
          initialValues={initialValues}
          onSubmit={handleTwilioEmailConfiguration}
          enableReinitialize
        >
          {({ isSubmitting, handleReset }) => (
            <Form>
              <Stack mt={5} spacing={5}>
                <CustomTextInput
                  name="email"
                  label="Email"
                  placeholder="Enter email"
                  isRequired
                />
                <CustomTextInput
                  name="api_key"
                  label="API key"
                  type="password"
                  isRequired
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
          serviceType={messagingProviders.twilio_email}
        />
      ) : null}
    </Box>
  );
};

export default TwilioEmailConfiguration;
