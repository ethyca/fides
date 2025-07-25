import { AntButton as Button, Box, Heading, HStack, useToast } from "fidesui";
import { Form, Formik } from "formik";
import { isEmpty, isUndefined, mapValues, omitBy } from "lodash";
import { useRouter } from "next/router";
import { useState } from "react";

import { CustomTextInput } from "~/features/common/form/inputs";
import { isErrorResult } from "~/features/common/helpers";
import { useAPIHelper } from "~/features/common/hooks";
import { MESSAGING_PROVIDERS_ROUTE } from "~/features/common/nav/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import MailgunIcon from "~/features/messaging/MailgunIcon";

import { messagingProviders } from "./constants";
import {
  useCreateMessagingConfigurationMutation,
  useGetMessagingConfigurationByKeyQuery,
  useUpdateDefaultMessagingConfigurationMutation,
  useUpdateMessagingConfigurationSecretsByKeyMutation,
} from "./messaging.slice";

interface MailgunMessagingFormProps {
  configKey?: string; // If provided, we're in edit mode
}

const MailgunMessagingForm = ({ configKey }: MailgunMessagingFormProps) => {
  const router = useRouter();
  const toast = useToast();
  const { handleError } = useAPIHelper();

  const [createMessagingConfiguration] =
    useCreateMessagingConfigurationMutation();
  const [updateDefaultMessagingConfiguration] =
    useUpdateDefaultMessagingConfigurationMutation();
  const [updateMessagingSecrets] =
    useUpdateMessagingConfigurationSecretsByKeyMutation();

  const isEditMode = !!configKey;

  // Fetch existing config data in edit mode
  const { data: existingConfig } = useGetMessagingConfigurationByKeyQuery(
    { key: configKey! },
    { skip: !configKey },
  );

  // Exclude secrets that haven't changed from placeholder values
  const excludeUnchangedSecrets = (secretsValues: any) =>
    omitBy(
      mapValues(secretsValues, (value) => {
        // Don't send placeholder values
        return isEditMode && value === "**********" ? undefined : value;
      }),
      isUndefined,
    );

  const handleMailgunConfiguration = async (values: {
    domain: string;
    mailgun_api_key: string;
  }) => {
    try {
      if (isEditMode && configKey) {
        // Edit mode: split updates between details and secrets
        const promises = [];

        // Update domain if changed
        const currentDomain = existingConfig?.details?.domain || "";
        if (values.domain !== currentDomain && values.domain.trim() !== "") {
          promises.push(
            updateDefaultMessagingConfiguration({
              service_type: messagingProviders.mailgun,
              details: {
                is_eu_domain: "false",
                domain: values.domain,
              },
            }),
          );
        }

        // Only update secrets that aren't placeholders
        const newSecrets = excludeUnchangedSecrets({
          mailgun_api_key: values.mailgun_api_key,
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
          toast(successToastParams("No changes to save."));
          return;
        }

        const results = await Promise.all(promises);
        const hasError = results.some((result) => isErrorResult(result));

        if (hasError) {
          const errorResult = results.find((result) => isErrorResult(result));
          handleError(errorResult?.error);
        } else {
          toast(
            successToastParams("Mailgun configuration successfully updated."),
          );
          router.push(MESSAGING_PROVIDERS_ROUTE);
        }
      } else {
        // Create mode
        const config = {
          service_type: messagingProviders.mailgun,
          details: {
            is_eu_domain: "false",
            domain: values.domain,
          },
          secrets: {
            mailgun_api_key: values.mailgun_api_key,
          },
        };

        const result = await createMessagingConfiguration(config);

        if (isErrorResult(result)) {
          handleError(result.error);
        } else {
          toast(
            successToastParams("Mailgun configuration successfully created."),
          );
          router.push(MESSAGING_PROVIDERS_ROUTE);
        }
      }
    } catch (error) {
      handleError(error);
    }
  };

  const initialValues = {
    domain: existingConfig?.details?.domain || "",
    mailgun_api_key: isEditMode ? "**********" : "",
  };

  const hasChanges = (values: typeof initialValues) => {
    if (!isEditMode) {
      return true; // Always allow save in create mode
    }

    const currentDomain = existingConfig?.details?.domain || "";
    const domainChanged = values.domain !== currentDomain;
    const apiKeyChanged =
      values.mailgun_api_key !== "**********" &&
      values.mailgun_api_key.trim() !== "";
    return domainChanged || apiKeyChanged;
  };

  return (
    <Box>
      <Formik
        initialValues={initialValues}
        onSubmit={handleMailgunConfiguration}
        enableReinitialize
      >
        {({ isSubmitting, values }) => (
          <Form>
            <Box>
              <Box
                maxWidth="720px"
                border="1px"
                borderColor="gray.200"
                borderRadius={6}
                overflow="visible"
                mt={6}
              >
                <Box
                  backgroundColor="gray.50"
                  px={6}
                  py={4}
                  display="flex"
                  flexDirection="row"
                  alignItems="center"
                  borderBottom="1px"
                  borderColor="gray.200"
                  borderTopRadius={6}
                >
                  <HStack>
                    <MailgunIcon />
                    <Heading as="h3" size="xs">
                      Mailgun email messaging configuration
                    </Heading>
                  </HStack>
                </Box>

                <Box px={6} py={6}>
                  <Box mb={4}>
                    <CustomTextInput
                      name="domain"
                      label="Domain"
                      placeholder={
                        isEditMode ? "Enter new domain" : "Enter domain"
                      }
                      variant="stacked"
                      isRequired
                    />
                  </Box>
                  <CustomTextInput
                    name="mailgun_api_key"
                    label="API key"
                    placeholder={
                      isEditMode ? "Enter new API key" : "Enter API key"
                    }
                    type="password"
                    variant="stacked"
                    isRequired
                  />

                  <Box mt={6}>
                    <Button
                      onClick={() => router.push(MESSAGING_PROVIDERS_ROUTE)}
                      className="mr-2"
                    >
                      Cancel
                    </Button>
                    <Button
                      disabled={isSubmitting || !hasChanges(values)}
                      htmlType="submit"
                      type="primary"
                      data-testid="save-btn"
                    >
                      Save
                    </Button>
                  </Box>
                </Box>
              </Box>
            </Box>
          </Form>
        )}
      </Formik>
    </Box>
  );
};

export default MailgunMessagingForm;
