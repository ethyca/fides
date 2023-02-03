import { Box, Button, Divider, Heading, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useState } from "react";

import { CustomTextInput } from "~/features/common/form/inputs";
import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import {
  useCreateMessagingConfigurationMutation,
  useCreateMessagingConfigurationSecretsMutation,
  // useGetMessagingConfigurationDetailsQuery,
} from "~/features/privacy-requests/privacy-requests.slice";

const MailgunEmailConfiguration = () => {
  const { successAlert } = useAlert();
  const [configurationStep, setConfigurationStep] = useState("");
  const { handleError } = useAPIHelper();
  // const { data: messagingDetails } = useGetMessagingConfigurationDetailsQuery({
  //   type: "mailgun",
  // });
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
      // setConfigurationStep("testConnection");
    }
  };

  // const handleTestConnection = () => {
  //   setConfigurationStep("4");
  // };

  const initialValues = {
    // domain: messagingDetails.domain ?? "",
    domain: "",
  };

  const initialAPIKeyValue = {
    // api_key: messagingDetails.api_key ?? "",
    api_key: "",
  };

  // const initialEmailValue = {
  //   email: email ?? "",
  // };

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
      {configurationStep === "apiKey" ||
      configurationStep === "testConnection" ? (
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
      {/* This will be added in the next sprint
      {configurationStep === "testConnection" ? (
        <>
          <Divider />
          <Heading fontSize="md" fontWeight="semibold" mt={10}>
            Test connection
          </Heading>
          <Stack>
            <Formik
              initialValues={initialEmailValue}
              onSubmit={handleTestConnection}
            >
              {({ isSubmitting, resetForm }) => (
                <Form>
                  <CustomTextInput
                    name="email"
                    label="Email"
                    placeholder="youremail@domain.com"
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
      ) : null} */}
    </Box>
  );
};

export default MailgunEmailConfiguration;
