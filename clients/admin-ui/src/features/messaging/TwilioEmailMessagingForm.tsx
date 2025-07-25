import { AntButton as Button, Box, Heading, HStack, useToast } from "fidesui";
import { Form, Formik } from "formik";
import { isEmpty, isUndefined, mapValues, omitBy } from "lodash";
import { useRouter } from "next/router";

import { CustomTextInput } from "~/features/common/form/inputs";
import { isErrorResult } from "~/features/common/helpers";
import { useAPIHelper } from "~/features/common/hooks";
import { MESSAGING_PROVIDERS_ROUTE } from "~/features/common/nav/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import TwilioIcon from "~/features/messaging/TwilioIcon";

import { messagingProviders } from "./constants";
import {
  useCreateMessagingConfigurationMutation,
  useGetMessagingConfigurationByKeyQuery,
  useUpdateDefaultMessagingConfigurationMutation,
  useUpdateMessagingConfigurationSecretsByKeyMutation,
} from "./messaging.slice";

interface TwilioEmailMessagingFormProps {
  configKey?: string; // If provided, we're in edit mode
}

const TwilioEmailMessagingForm = ({
  configKey,
}: TwilioEmailMessagingFormProps) => {
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

  const handleTwilioEmailConfiguration = async (values: {
    email: string;
    twilio_api_key: string;
  }) => {
    try {
      if (isEditMode && configKey) {
        // Edit mode: split updates between details and secrets
        const promises = [];

        // Update email if changed
        const currentEmail = existingConfig?.details?.twilio_email_from || "";
        if (values.email !== currentEmail && values.email.trim() !== "") {
          promises.push(
            updateDefaultMessagingConfiguration({
              service_type: messagingProviders.twilio_email,
              details: {
                twilio_email_from: values.email,
              },
            }),
          );
        }

        // Only update secrets that aren't placeholders
        const newSecrets = excludeUnchangedSecrets({
          api_key: values.twilio_api_key,
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
            successToastParams(
              "Twilio email configuration successfully updated.",
            ),
          );
          router.push(MESSAGING_PROVIDERS_ROUTE);
        }
      } else {
        // Create mode
        const config = {
          service_type: messagingProviders.twilio_email,
          details: {
            twilio_email_from: values.email,
          },
          secrets: {
            api_key: values.twilio_api_key,
          },
        };

        const result = await createMessagingConfiguration(config);

        if (isErrorResult(result)) {
          handleError(result.error);
        } else {
          toast(
            successToastParams(
              "Twilio email configuration successfully created.",
            ),
          );
          router.push(MESSAGING_PROVIDERS_ROUTE);
        }
      }
    } catch (error) {
      handleError(error);
    }
  };

  const initialValues = {
    email: existingConfig?.details?.twilio_email_from || "",
    twilio_api_key: isEditMode ? "**********" : "",
  };

  const hasChanges = (values: typeof initialValues) => {
    if (!isEditMode) {
      return true; // Always allow save in create mode
    }

    const currentEmail = existingConfig?.details?.twilio_email_from || "";
    const emailChanged = values.email !== currentEmail;
    const apiKeyChanged =
      values.twilio_api_key !== "**********" &&
      values.twilio_api_key.trim() !== "";
    return emailChanged || apiKeyChanged;
  };

  return (
    <Box>
      <Formik
        initialValues={initialValues}
        onSubmit={handleTwilioEmailConfiguration}
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
                    <TwilioIcon />
                    <Heading as="h3" size="xs">
                      Twilio email messaging configuration
                    </Heading>
                  </HStack>
                </Box>

                <Box px={6} py={6}>
                  <Box mb={4}>
                    <CustomTextInput
                      name="email"
                      label="Email"
                      placeholder={
                        isEditMode ? "Enter new email" : "Enter email"
                      }
                      variant="stacked"
                      isRequired
                    />
                  </Box>
                  <CustomTextInput
                    name="twilio_api_key"
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

export default TwilioEmailMessagingForm;
