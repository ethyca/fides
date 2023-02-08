import { Box, Button, Divider, Heading, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useState } from "react";

import { CustomTextInput } from "~/features/common/form/inputs";
import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import {
  useCreateMessagingConfigurationMutation,
  useCreateMessagingConfigurationSecretsMutation,
  useGetMessagingConfigurationDetailsQuery,
} from "~/features/privacy-requests/privacy-requests.slice";

type ConnectionStep = "" | "apiKey" | "testConnection";

const MailgunEmailConfiguration = () => {
  const { successAlert } = useAlert();
  const [configurationStep, setConfigurationStep] =
    useState<ConnectionStep>("");
  const { handleError } = useAPIHelper();
  const { data: messagingDetails } = useGetMessagingConfigurationDetailsQuery({
    type: "mailgun",
  });
  const [createMessagingConfiguration] =
    useCreateMessagingConfigurationMutation();
  const [createMessagingConfigurationSecrets] =
    useCreateMessagingConfigurationSecretsMutation();

  const handleMailgunConfiguration = async (value: { domain: string }) => {
    const result = await createMessagingConfiguration({
      type: "mailgun",
      details: {
        is_eu_domain: "false",
        domain: value.domain,
      },
    });

    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      successAlert(
        `Mailgun email successfully updated. You can now enter your security key.`
      );
      setConfigurationStep("apiKey");
    }
  };

  const handleMailgunAPIKeyConfiguration = async (value: {
    api_key: string;
  }) => {
    const result = await createMessagingConfigurationSecrets({
      mailgun_api_key: value.api_key,
    });

    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      successAlert(`Mailgun security key successfully updated.`);
    }
  };

  const initialValues = {
    domain: messagingDetails?.details.domain ?? "",
  };

  const initialAPIKeyValue = {
    api_key: messagingDetails?.key ?? "",
  };

  return (
    <Box>
      <Heading fontSize="md" fontWeight="semibold" mt={10}>
        Mailgun messaging configuration
      </Heading>
      <Stack>
        <Formik
          initialValues={initialValues}
          onSubmit={handleMailgunConfiguration}
        >
          {({ isSubmitting, resetForm }) => (
            <Form>
              <Stack mt={5} spacing={5}>
                <CustomTextInput
                  name="domain"
                  label="Domain"
                  placeholder="Enter domain"
                />
              </Stack>
              <Box mt={10}>
                <Button
                  onClick={() => resetForm()}
                  mr={2}
                  size="sm"
                  variant="outline"
                >
                  Cancel
                </Button>
                <Button
                  isDisabled={isSubmitting}
                  type="submit"
                  colorScheme="primary"
                  size="sm"
                  data-testid="save-btn"
                >
                  Save
                </Button>
              </Box>
            </Form>
          )}
        </Formik>
      </Stack>
      {configurationStep === "apiKey" ? (
        // TODO: configurationStep === "testConnection" will be set after https://github.com/ethyca/fides/issues/2237
        <>
          <Divider />
          <Heading fontSize="md" fontWeight="semibold" mt={10}>
            Security key
          </Heading>
          <Stack>
            <Formik
              initialValues={initialAPIKeyValue}
              onSubmit={handleMailgunAPIKeyConfiguration}
            >
              {({ isSubmitting, resetForm }) => (
                <Form>
                  <CustomTextInput
                    name="api_key"
                    label="API key"
                    placeholder="Optional"
                    type="password"
                  />
                  <Button
                    onClick={() => resetForm()}
                    mr={2}
                    size="sm"
                    variant="outline"
                  >
                    Cancel
                  </Button>
                  <Button
                    isDisabled={isSubmitting}
                    type="submit"
                    colorScheme="primary"
                    size="sm"
                    data-testid="save-btn"
                  >
                    Save
                  </Button>
                </Form>
              )}
            </Formik>
          </Stack>
        </>
      ) : null}
    </Box>
  );
};

export default MailgunEmailConfiguration;
