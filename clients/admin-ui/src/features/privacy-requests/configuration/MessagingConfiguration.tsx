import { Box, Heading, Radio, RadioGroup, Stack, Text } from "fidesui";
import { useEffect, useState } from "react";

import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import Layout from "~/features/common/Layout";
import {
  PRIVACY_REQUESTS_CONFIGURATION_ROUTE,
  PRIVACY_REQUESTS_ROUTE,
} from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import { messagingProviders } from "~/features/privacy-requests/constants";
import {
  useCreateMessagingConfigurationMutation,
  useGetActiveMessagingProviderQuery,
  usePatchConfigurationSettingsMutation,
} from "~/features/privacy-requests/privacy-requests.slice";

import MailgunEmailConfiguration from "./MailgunEmailConfiguration";
import TwilioEmailConfiguration from "./TwilioEmailConfiguration";
import TwilioSMSConfiguration from "./TwilioSMS";

const MessagingConfiguration = () => {
  const { successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const [messagingValue, setMessagingValue] = useState("");
  const [createMessagingConfiguration] =
    useCreateMessagingConfigurationMutation();
  const [saveActiveConfiguration] = usePatchConfigurationSettingsMutation();
  const { data: activeMessagingProvider } =
    useGetActiveMessagingProviderQuery();

  useEffect(() => {
    if (activeMessagingProvider) {
      setMessagingValue(activeMessagingProvider?.service_type);
    }
  }, [activeMessagingProvider]);

  const handleChange = async (value: string) => {
    const result = await saveActiveConfiguration({
      notifications: {
        notification_service_type: value,
        send_request_completion_notification: true,
        send_request_receipt_notification: true,
        send_request_review_notification: true,
      },
      execution: {
        subject_identity_verification_required: true,
      },
    });

    if (isErrorResult(result)) {
      handleError(result.error);
    } else if (value !== messagingProviders.twilio_text) {
      setMessagingValue(value);
    } else {
      const twilioTextResult = await createMessagingConfiguration({
        service_type: messagingProviders.twilio_text,
      });

      if (isErrorResult(twilioTextResult)) {
        handleError(twilioTextResult.error);
      } else {
        successAlert(`Messaging provider saved successfully.`);
        setMessagingValue(value);
      }
    }
  };

  return (
    <Layout title="Configure Privacy Requests - Messaging">
      <PageHeader
        heading="Privacy Requests"
        breadcrumbItems={[
          { title: "All requests", href: PRIVACY_REQUESTS_ROUTE },
          {
            title: "Configure requests",
            href: PRIVACY_REQUESTS_CONFIGURATION_ROUTE,
          },
          { title: "Messaging" },
        ]}
      />
      <Heading mb={5} fontSize="md" fontWeight="semibold">
        Configure your messaging provider
      </Heading>

      <Box display="flex" flexDirection="column" width="50%">
        <Box>
          Fides requires a messsaging provider for sending processing notices to
          privacy request subjects, and allows for Subject Identity Verification
          in privacy requests. Please follow the{" "}
          <Text as="span" color="complimentary.500">
            documentation
          </Text>{" "}
          to setup a messaging service that Fides supports. Ensure you have
          completed the setup for the preferred messaging provider and have the
          details handy prior to the following steps.
        </Box>
        <Heading fontSize="md" fontWeight="semibold" mt={10}>
          Choose service type to configure
        </Heading>
        <RadioGroup
          onChange={handleChange}
          value={messagingValue}
          data-testid="privacy-requests-messaging-provider-selection"
          colorScheme="primary"
          p={3}
        >
          <Stack direction="row">
            <Radio
              key={messagingProviders.mailgun}
              value={messagingProviders.mailgun}
              data-testid="option-mailgun"
              mr={5}
            >
              Mailgun Email
            </Radio>
            <Radio
              key={messagingProviders.twilio_email}
              value={messagingProviders.twilio_email}
              data-testid="option-twilio-email"
            >
              Twilio Email
            </Radio>
            <Radio
              key={messagingProviders.twilio_text}
              value={messagingProviders.twilio_text}
              data-testid="option-twilio-sms"
            >
              Twilio SMS
            </Radio>
          </Stack>
        </RadioGroup>
        {messagingValue === messagingProviders.mailgun ? (
          <MailgunEmailConfiguration />
        ) : null}
        {messagingValue === messagingProviders.twilio_email ? (
          <TwilioEmailConfiguration />
        ) : null}
        {messagingValue === messagingProviders.twilio_text ? (
          <TwilioSMSConfiguration />
        ) : null}
      </Box>
    </Layout>
  );
};

export default MessagingConfiguration;
