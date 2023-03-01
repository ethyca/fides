import { Button, Divider, Heading, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";

import { CustomTextInput } from "~/features/common/form/inputs";
import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import { useCreateTestConnectionMessageMutation } from "~/features/privacy-requests/privacy-requests.slice";

const TestMessagingProviderConnectionButton = (messagingDetails: any) => {
  const { successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const [createTestConnectionMessage] =
    useCreateTestConnectionMessageMutation();

  const initialEmailValue = {
    email: messagingDetails?.email ?? "",
  };

  const handleTestConnection = async () => {
    const result = await createTestConnectionMessage({
      // test
    });

    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      successAlert(`Test message successfully sent.`);
    }
    // I can enter a test identifier (Email or SMS) based on the messaging service type.
    // I can click on test the configuration to send a test message.
  };

  return (
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
              {/* Should this input be phone number if coming from SMS path or is it always an email? */}
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
  );
};

export default TestMessagingProviderConnectionButton;
