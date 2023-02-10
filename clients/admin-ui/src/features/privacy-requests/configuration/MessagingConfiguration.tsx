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
import { useState } from "react";

import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import Layout from "~/features/common/Layout";
import {
  useCreateConfigurationSettingsMutation,
  useCreateMessagingConfigurationMutation,
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

  const handleChange = async (value: string) => {
    const result = await saveActiveConfiguration({
      fides: {
        notifications: {
          notification_service_type: value,
          send_request_completion_notification: true,
          send_request_receipt_notification: true,
          send_request_review_notification: true,
          subject_identity_verification_required: true,
        },
      },
    });

    if (isErrorResult(result)) {
      handleError(result.error);
    } else if (value !== "twilio_text") {
      successAlert(`Configured storage type successfully.`);
      setMessagingValue(value);
    } else {
      const twilioTextResult = await createMessagingConfiguration({
        type: "twilio_text",
      });

      if (isErrorResult(twilioTextResult)) {
        handleError(twilioTextResult.error);
      } else {
        successAlert(`Configure messaging provider saved successfully.`);
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
              key="mailgun-email"
              value="mailgun-email"
              data-testid="option-mailgun-email"
              mr={5}
            >
              Mailgun email
            </Radio>
            <Radio
              key="twilio-email"
              value="twilio-email"
              data-testid="option-twilio-email"
            >
              Twilio email
            </Radio>
            <Radio
              key="twilio-text"
              value="twilio-text"
              data-testid="option-twilio-text"
            >
              Twilio sms
            </Radio>
          </Stack>
        </RadioGroup>
        {messagingValue === "mailgun-email" ? (
          <MailgunEmailConfiguration />
        ) : null}
        {messagingValue === "twilio-email" ? (
          <TwilioEmailConfiguration />
        ) : null}
        {messagingValue === "twilio-text" ? <TwilioSMSConfiguration /> : null}
      </Box>
    </Layout>
  );
};

export default MessagingConfiguration;
