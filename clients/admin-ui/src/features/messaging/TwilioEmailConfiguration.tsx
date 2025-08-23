import {
  AntButton as Button,
  Box,
  Heading,
  HStack,
  Stack,
  Text,
} from "fidesui";
import { Form, Formik } from "formik";
import { isEmpty, isUndefined, mapValues, omitBy } from "lodash";
import { useRouter } from "next/router";
import { useState } from "react";

import { CustomTextInput } from "~/features/common/form/inputs";
import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import { MESSAGING_PROVIDERS_ROUTE } from "~/features/common/nav/routes";
import TwilioIcon from "~/features/messaging/TwilioIcon";

import { messagingProviders } from "./constants";
import {
  useCreateMessagingConfigurationMutation,
  useGetMessagingConfigurationByKeyQuery,
  useGetMessagingConfigurationDetailsQuery,
  useUpdateMessagingConfigurationByKeyMutation,
  useUpdateMessagingConfigurationSecretsByKeyMutation,
} from "./messaging.slice";
import TestMessagingProviderConnectionButton from "./TestMessagingProviderConnectionButton";

interface TwilioEmailConfigurationProps {
  configKey?: string; // If provided, we're in edit mode
}

const TwilioEmailConfiguration = ({
  configKey,
}: TwilioEmailConfigurationProps) => {
  const router = useRouter();
  const [configurationStep, setConfigurationStep] = useState("");
  const { successAlert } = useAlert();
  const { handleError } = useAPIHelper();

  // For editing: fetch existing config by key
  const { data: existingConfig } = useGetMessagingConfigurationByKeyQuery(
    { key: configKey! },
    { skip: !configKey },
  );

  // For creating: fetch details by type (legacy approach)
  const { data: messagingDetails } = useGetMessagingConfigurationDetailsQuery(
    {
      type: messagingProviders.twilio_email,
    },
    { skip: !!configKey },
  );

  const [createMessagingConfiguration] =
    useCreateMessagingConfigurationMutation();
  const [updateMessagingConfiguration] =
    useUpdateMessagingConfigurationByKeyMutation();
  const [updateMessagingSecrets] =
    useUpdateMessagingConfigurationSecretsByKeyMutation();

  const isEditMode = !!configKey;
  const configData = isEditMode ? existingConfig : messagingDetails;

  // Exclude secrets that haven't changed from placeholder values
  const excludeUnchangedSecrets = (secretsValues: any) =>
    omitBy(
      mapValues(secretsValues, (value) => {
        // Don't send placeholder values
        return isEditMode && value === "**********" ? undefined : value;
      }),
      isUndefined,
    );

  const handleTwilioEmailConfiguration = async (value: {
    email: string;
    api_key: string;
  }) => {
    try {
      if (isEditMode && configKey) {
        // Edit mode: split updates between details and secrets
        const promises = [];

        // Update details if email changed
        const currentEmail = configData?.details?.twilio_email_from || "";
        if (value.email !== currentEmail) {
          promises.push(
            updateMessagingConfiguration({
              key: configKey,
              config: {
                service_type: messagingProviders.twilio_email,
                details: {
                  twilio_email_from: value.email,
                },
              },
            }),
          );
        }

        // Only update secrets that aren't placeholders
        const newSecrets = excludeUnchangedSecrets({ api_key: value.api_key });
        if (!isEmpty(newSecrets)) {
          promises.push(
            updateMessagingSecrets({
              key: configKey,
              secrets: newSecrets,
            }),
          );
        }

        if (promises.length === 0) {
          successAlert("No changes to save.");
          return;
        }

        const results = await Promise.all(promises);
        const hasError = results.some((result) => isErrorResult(result));

        if (hasError) {
          const errorResult = results.find((result) => isErrorResult(result));
          handleError(errorResult?.error);
        } else {
          successAlert("Twilio email configuration successfully updated.");
          setConfigurationStep("testConnection");
        }
      } else {
        // Create mode: original logic
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
          successAlert("Twilio email successfully created.");
          setConfigurationStep("testConnection");
        }
      }
    } catch (error) {
      handleError(error);
    }
  };

  const initialValues = {
    email: configData?.details?.twilio_email_from ?? "",
    api_key: isEditMode ? "**********" : "", // Show placeholder in edit mode
  };

  return (
    <Box>
      <Heading fontSize="md" fontWeight="semibold" mt={10}>
        <HStack>
          <TwilioIcon />
          <Text>Twilio email messaging configuration</Text>
        </HStack>
      </Heading>
      <Stack>
        <Formik
          initialValues={initialValues}
          onSubmit={handleTwilioEmailConfiguration}
          enableReinitialize
        >
          {({ isSubmitting, values }) => {
            // Detect if there are actual changes
            const hasChanges = () => {
              if (!isEditMode) {
                return true; // Always allow save in create mode
              }

              // Check if email changed
              const emailChanged =
                values.email !== (configData?.details?.twilio_email_from ?? "");

              // Check if API key changed (not just the placeholder)
              const apiKeyChanged =
                values.api_key !== "**********" && values.api_key.trim() !== "";

              return emailChanged || apiKeyChanged;
            };

            return (
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
                    placeholder={
                      isEditMode ? "Enter new API key" : "Enter API key"
                    }
                    isRequired
                  />
                </Stack>
                <Box mt={10}>
                  <Button
                    onClick={() => router.push(MESSAGING_PROVIDERS_ROUTE)}
                    className="mr-2"
                  >
                    Cancel
                  </Button>
                  <Button
                    disabled={isSubmitting || !hasChanges()}
                    htmlType="submit"
                    type="primary"
                    data-testid="save-btn"
                  >
                    Save
                  </Button>
                </Box>
              </Form>
            );
          }}
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
