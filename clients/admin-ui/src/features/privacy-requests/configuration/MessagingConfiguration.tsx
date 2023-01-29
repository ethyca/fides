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

import Layout from "~/features/common/Layout";

import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import {
  useCreateMessagingConfigurationMutation,
  useGetMessagingConfigurationDetailsQuery,
} from "../privacy-requests.slice";
import { useState } from "react";

interface MessagingData {}

const MessagingConfiguration = () => {
  const [existingMessagingData, setExistingMessagingData] =
    useState<MessagingData>();
  const [saveMessagingConfiguration, { isLoading }] =
    useCreateMessagingConfigurationMutation();
  const { data: existingData } = useGetMessagingConfigurationDetailsQuery(
    existingMessagingData
  );
  const { errorAlert, successAlert } = useAlert();

  const handleChange = async (value: string) => {
    const payload = await saveMessagingConfiguration({
      config_key: value,
    });
    if ("error" in payload) {
      errorAlert(
        getErrorMessage(payload.error),
        `Configuring storage type has failed to save due to the following:`
      );
    } else {
      successAlert(`Configure storage type saved successfully.`);
      setExistingMessagingData(existingData);
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
          Fides utilizes{" "}
          <Text as="span" color="complimentary.500">
            Mailgun
          </Text>{" "}
          to support email server configurations for sending processing notices
          to privacy request subjects, and allows for Subject Identity
          Verification in privacy requests. Ensure you register or use an
          existing Mailgun account prior to the following steps. If needed,
          follow the{" "}
          <Text as="span" color="complimentary.500">
            Mailgun documentation
          </Text>{" "}
          to create a new Domain Sending Key for Fides.
        </Box>
        <Heading mb={5} fontSize="2xl" fontWeight="semibold">
          Choose service type to configure
        </Heading>
        <RadioGroup
          //   isDisabled={isLoading}
          onChange={handleChange}
          value={existingMessagingData ?? undefined}
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
              key="twilio-sms"
              value="twilio-sms"
              data-testid="option-twilio-sms"
            >
              Twilio sms
            </Radio>
          </Stack>
        </RadioGroup>
      </Box>
    </Layout>
  );
};

export default MessagingConfiguration;
