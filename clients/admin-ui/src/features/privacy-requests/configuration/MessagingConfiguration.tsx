import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Heading,
  Radio,
  RadioGroup,
  Stack,
  Text,
} from "@fidesui/react";
import NextLink from "next/link";
import { useEffect, useState } from "react";

import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import Layout from "~/features/common/Layout";
import {
  useCreateConfigurationSettingsMutation,
  useCreateMessagingConfigurationMutation,
  useGetActiveMessagingProviderQuery,
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
  const [saveActiveConfiguration] = useCreateConfigurationSettingsMutation();
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
    } else if (value !== "TWILIO_TEXT") {
      setMessagingValue(value);
    } else {
      const twilioTextResult = await createMessagingConfiguration({
        service_type: "TWILIO_TEXT",
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
      <Box mb={8}>
        <Breadcrumb fontWeight="medium" fontSize="sm" color="gray.600">
          <BreadcrumbItem>
            <BreadcrumbLink as={NextLink} href="/privacy-requests">
              Privacy requests
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <BreadcrumbLink as={NextLink} href="/privacy-requests/configure">
              Configuration
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbItem color="complimentary.500">
            <BreadcrumbLink
              as={NextLink}
              href="/privacy-requests/configure/messaging"
              isCurrentPage
            >
              Configure messaging provider
            </BreadcrumbLink>
          </BreadcrumbItem>
        </Breadcrumb>
      </Box>

      <Heading mb={5} fontSize="2xl" fontWeight="semibold">
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
          colorScheme="secondary"
          p={3}
        >
          <Stack direction="row">
            <Radio
              key="MAILGUN"
              value="MAILGUN"
              data-testid="option-MAILGUN"
              mr={5}
            >
              Mailgun email
            </Radio>
            <Radio
              key="TWILIO_EMAIL"
              value="TWILIO_EMAIL"
              data-testid="option-TWILIO_EMAIL"
            >
              Twilio email
            </Radio>
            <Radio
              key="TWILIO_TEXT"
              value="TWILIO_TEXT"
              data-testid="option-TWILIO_TEXT"
            >
              Twilio sms
            </Radio>
          </Stack>
        </RadioGroup>
        {messagingValue === "MAILGUN" ? <MailgunEmailConfiguration /> : null}
        {messagingValue === "TWILIO_EMAIL" ? (
          <TwilioEmailConfiguration />
        ) : null}
        {messagingValue === "TWILIO_TEXT" ? <TwilioSMSConfiguration /> : null}
      </Box>
    </Layout>
  );
};

export default MessagingConfiguration;
