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
import TwilioIcon from "~/features/messaging/TwilioIcon";

import { messagingProviders } from "./constants";
import {
  useCreateMessagingConfigurationMutation,
  useUpdateMessagingConfigurationSecretsByKeyMutation,
} from "./messaging.slice";

interface TwilioSMSMessagingFormProps {
  configKey?: string; // If provided, we're in edit mode
}

const TwilioSMSMessagingForm = ({ configKey }: TwilioSMSMessagingFormProps) => {
  const router = useRouter();
  const toast = useToast();
  const { handleError } = useAPIHelper();

  const [createMessagingConfiguration] =
    useCreateMessagingConfigurationMutation();
  const [updateMessagingSecrets] =
    useUpdateMessagingConfigurationSecretsByKeyMutation();

  const isEditMode = !!configKey;

  // Exclude secrets that haven't changed from placeholder values
  const excludeUnchangedSecrets = (secretsValues: any) =>
    omitBy(
      mapValues(secretsValues, (value) => {
        // Don't send placeholder values
        return isEditMode && value === "**********" ? undefined : value;
      }),
      isUndefined,
    );

  const handleTwilioSMSConfiguration = async (values: {
    account_sid: string;
    auth_token: string;
    messaging_service_sid: string;
    phone: string;
  }) => {
    try {
      if (isEditMode && configKey) {
        // Edit mode: only update secrets that aren't placeholders
        const secretsToUpdate = {
          twilio_account_sid: values.account_sid,
          twilio_auth_token: values.auth_token,
          twilio_messaging_service_sid: values.messaging_service_sid,
          twilio_sender_phone_number: values.phone,
        };

        const newSecrets = excludeUnchangedSecrets(secretsToUpdate);

        if (isEmpty(newSecrets)) {
          toast(successToastParams("No changes to save."));
          return;
        }

        const result = await updateMessagingSecrets({
          key: configKey,
          secrets: newSecrets,
        });

        if (isErrorResult(result)) {
          handleError(result.error);
        } else {
          toast(
            successToastParams(
              "Twilio SMS configuration successfully updated.",
            ),
          );
          router.push(MESSAGING_PROVIDERS_ROUTE);
        }
      } else {
        // Create mode
        const config = {
          service_type: messagingProviders.twilio_text,
          secrets: {
            twilio_account_sid: values.account_sid,
            twilio_auth_token: values.auth_token,
            twilio_messaging_service_sid: values.messaging_service_sid,
            twilio_sender_phone_number: values.phone,
          },
        };

        const result = await createMessagingConfiguration(config);

        if (isErrorResult(result)) {
          handleError(result.error);
        } else {
          toast(
            successToastParams(
              "Twilio SMS configuration successfully created.",
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
    account_sid: isEditMode ? "**********" : "",
    auth_token: isEditMode ? "**********" : "",
    messaging_service_sid: isEditMode ? "**********" : "",
    phone: isEditMode ? "**********" : "",
  };

  const hasChanges = (values: typeof initialValues) => {
    if (!isEditMode) {
      return true; // Always allow save in create mode
    }

    const accountSidChanged =
      values.account_sid !== "**********" && values.account_sid.trim() !== "";
    const authTokenChanged =
      values.auth_token !== "**********" && values.auth_token.trim() !== "";
    const messagingServiceSidChanged =
      values.messaging_service_sid !== "**********" &&
      values.messaging_service_sid.trim() !== "";
    const phoneChanged =
      values.phone !== "**********" && values.phone.trim() !== "";

    return (
      accountSidChanged ||
      authTokenChanged ||
      messagingServiceSidChanged ||
      phoneChanged
    );
  };

  return (
    <Box>
      <Formik
        initialValues={initialValues}
        onSubmit={handleTwilioSMSConfiguration}
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
                      Twilio SMS messaging configuration
                    </Heading>
                  </HStack>
                </Box>

                <Box px={6} py={6}>
                  <Box mb={4}>
                    <CustomTextInput
                      name="account_sid"
                      label="Account SID"
                      placeholder={
                        isEditMode
                          ? "Enter new account SID"
                          : "Enter account SID"
                      }
                      variant="stacked"
                      isRequired
                    />
                  </Box>
                  <Box mb={4}>
                    <CustomTextInput
                      name="auth_token"
                      label="Auth token"
                      placeholder={
                        isEditMode ? "Enter new auth token" : "Enter auth token"
                      }
                      type="password"
                      variant="stacked"
                      isRequired
                    />
                  </Box>
                  <Box mb={4}>
                    <CustomTextInput
                      name="messaging_service_sid"
                      label="Messaging service SID"
                      placeholder={
                        isEditMode
                          ? "Enter new messaging service SID"
                          : "Enter messaging service SID"
                      }
                      variant="stacked"
                      isRequired={false}
                    />
                  </Box>
                  <CustomTextInput
                    name="phone"
                    label="Phone number"
                    placeholder={
                      isEditMode
                        ? "Enter new phone number"
                        : "Enter phone number"
                    }
                    variant="stacked"
                    isRequired={false}
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

export default TwilioSMSMessagingForm;
