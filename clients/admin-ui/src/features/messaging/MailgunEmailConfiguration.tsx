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
import MailgunIcon from "~/features/messaging/MailgunIcon";

import { messagingProviders } from "./constants";
import {
  useCreateMessagingConfigurationMutation,
  useGetMessagingConfigurationByKeyQuery,
  useGetMessagingConfigurationDetailsQuery,
  useUpdateMessagingConfigurationByKeyMutation,
  useUpdateMessagingConfigurationSecretsByKeyMutation,
} from "./messaging.slice";
import TestMessagingProviderConnectionButton from "./TestMessagingProviderConnectionButton";

type ConnectionStep = "" | "apiKey" | "testConnection";

interface MailgunEmailConfigurationProps {
  configKey?: string; // If provided, we're in edit mode
}

const MailgunEmailConfiguration = ({
  configKey,
}: MailgunEmailConfigurationProps) => {
  const router = useRouter();
  const { successAlert } = useAlert();
  const [configurationStep, setConfigurationStep] =
    useState<ConnectionStep>("");
  const { handleError } = useAPIHelper();

  // For editing: fetch existing config by key
  const { data: existingConfig } = useGetMessagingConfigurationByKeyQuery(
    { key: configKey! },
    { skip: !configKey },
  );

  // For creating: fetch details by type (legacy approach)
  const { data: messagingDetails } = useGetMessagingConfigurationDetailsQuery(
    {
      type: messagingProviders.mailgun,
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

  const handleMailgunConfiguration = async (value: {
    domain: string;
    api_key: string;
  }) => {
    try {
      if (isEditMode && configKey) {
        // Edit mode: split updates between details and secrets
        const promises = [];

        // Update details if domain changed
        const currentDomain = configData?.details?.domain || "";
        if (value.domain !== currentDomain) {
          promises.push(
            updateMessagingConfiguration({
              key: configKey,
              config: {
                service_type: messagingProviders.mailgun,
                details: {
                  is_eu_domain: "false",
                  domain: value.domain,
                },
              },
            }),
          );
        }

        // Only update secrets that aren't placeholders
        const newSecrets = excludeUnchangedSecrets({
          mailgun_api_key: value.api_key,
        });
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
          successAlert("Mailgun configuration successfully updated.");
          setConfigurationStep("testConnection");
        }
      } else {
        // Create mode: original logic
        const result = await createMessagingConfiguration({
          service_type: messagingProviders.mailgun,
          details: {
            is_eu_domain: "false",
            domain: value.domain,
          },
          secrets: {
            mailgun_api_key: value.api_key,
          },
        });

        if (isErrorResult(result)) {
          handleError(result.error);
        } else {
          successAlert("Mailgun email successfully created.");
          setConfigurationStep("testConnection");
        }
      }
    } catch (error) {
      handleError(error);
    }
  };

  const initialValues = {
    domain: configData?.details?.domain ?? "",
    api_key: isEditMode ? "**********" : "", // Show placeholder in edit mode
  };

  return (
    <Box>
      <Heading fontSize="md" fontWeight="semibold" mt={10}>
        <HStack>
          <MailgunIcon />
          <Text>Mailgun messaging configuration</Text>
        </HStack>
      </Heading>
      <Stack>
        <Formik
          initialValues={initialValues}
          onSubmit={handleMailgunConfiguration}
          enableReinitialize
        >
          {({ isSubmitting, values }) => {
            // Detect if there are actual changes
            const hasChanges = () => {
              if (!isEditMode) {
                return true; // Always allow save in create mode
              }

              // Check if domain changed
              const domainChanged =
                values.domain !== (configData?.details?.domain ?? "");

              // Check if API key changed (not just the placeholder)
              const apiKeyChanged =
                values.api_key !== "**********" && values.api_key.trim() !== "";

              return domainChanged || apiKeyChanged;
            };

            return (
              <Form>
                <Stack mt={5} spacing={5}>
                  <CustomTextInput
                    name="domain"
                    label="Domain"
                    placeholder="Enter domain"
                    data-testid="input-domain"
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
                    htmlType="submit"
                    disabled={isSubmitting || !hasChanges()}
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
      {configurationStep === "testConnection" && (
        <TestMessagingProviderConnectionButton
          serviceType={messagingProviders.mailgun}
        />
      )}
    </Box>
  );
};

export default MailgunEmailConfiguration;
