import { AntSelect as Select, Box, Heading } from "fidesui";
import { useEffect, useState } from "react";

import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import Layout from "~/features/common/Layout";
import { messagingProviders } from "~/features/privacy-requests/constants";

import BackButton from "../common/nav/v2/BackButton";
import { MESSAGING_CONFIGURATION_ROUTE } from "../common/nav/v2/routes";
import { usePatchConfigurationSettingsMutation } from "../privacy-requests";
import MailgunEmailConfiguration from "./MailgunEmailConfiguration";
import {
  useCreateMessagingConfigurationMutation,
  useGetActiveMessagingProviderQuery,
} from "./messaging.slice";
import TwilioEmailConfiguration from "./TwilioEmailConfiguration";
import TwilioSMSConfiguration from "./TwilioSMS";

export const CreateMessagingConfiguration = () => {
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
          onChange={handleChange}
          placeholder="Select messaging provider..."
          options={[
            { value: messagingProviders.mailgun, label: "Mailgun Email" },
            { value: messagingProviders.twilio_email, label: "Twilio Email" },
            { value: messagingProviders.twilio_text, label: "Twilio SMS" },
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
