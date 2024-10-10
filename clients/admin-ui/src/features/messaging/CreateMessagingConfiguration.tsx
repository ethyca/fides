import { AntSelect as Select, Box, Heading } from "fidesui";
import { useState } from "react";

import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import Layout from "~/features/common/Layout";

import BackButton from "../common/nav/v2/BackButton";
import { MESSAGING_CONFIGURATION_ROUTE } from "../common/nav/v2/routes";
import { messagingProviderLabels, messagingProviders } from "./constants";
import MailgunEmailConfiguration from "./MailgunEmailConfiguration";
import {
  useCreateMessagingConfigurationMutation,
} from "./messaging.slice";
import TwilioEmailConfiguration from "./TwilioEmailConfiguration";
import TwilioSMSConfiguration from "./TwilioSMS";

export const CreateMessagingConfiguration = () => {
  const { successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const [messagingValue, setMessagingValue] = useState("");
  const [createMessagingConfiguration] =
    useCreateMessagingConfigurationMutation();

  const handleChange = async (value: string) => {
    if (value !== messagingProviders.twilio_text) {
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
    <Layout title="Create Messaging Configuration">
      <BackButton backPath={MESSAGING_CONFIGURATION_ROUTE} />

      <Heading mb={5} fontSize="2xl" fontWeight="semibold">
        Configure your messaging provider
      </Heading>

      <Box display="flex" flexDirection="column" width="50%">
        <Heading fontSize="md" fontWeight="semibold" mt={10}>
          Choose service type to configure
        </Heading>
        <Select
          className="mt-4"
          data-testid="messaging-provider-select"
          onChange={handleChange}
          placeholder="Select messaging provider..."
          options={[
            {
              value: messagingProviders.mailgun,
              label: messagingProviderLabels.mailgun,
            },
            {
              value: messagingProviders.twilio_email,
              label: messagingProviderLabels.twilio_email,
            },
            {
              value: messagingProviders.twilio_text,
              label: messagingProviderLabels.twilio_text,
            },
          ]}
        />
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
