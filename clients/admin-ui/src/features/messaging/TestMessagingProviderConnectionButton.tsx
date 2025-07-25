import {
  AntButton as Button,
  Box,
  Divider,
  Heading,
  Stack,
  useToast,
} from "fidesui";
import { Form, Formik } from "formik";

import { CustomTextInput } from "~/features/common/form/inputs";
import { isErrorResult } from "~/features/common/helpers";
import { useAPIHelper } from "~/features/common/hooks";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { messagingProviders } from "~/features/messaging/constants";

import { useCreateTestConnectionMessageMutation } from "./messaging.slice";

export interface TestMessagingProviderConnectionButtonProps {
  serviceType: string | undefined;
  isModal?: boolean;
  onClose?: () => void;
}

const TestMessagingProviderConnectionButton = ({
  serviceType,
  isModal,
  onClose,
}: TestMessagingProviderConnectionButtonProps) => {
  const toast = useToast();
  const { handleError } = useAPIHelper();
  const [createTestConnectionMessage] =
    useCreateTestConnectionMessageMutation();

  if (!serviceType) {
    return null;
  }

  const emailProvider =
    serviceType === messagingProviders.twilio_email ||
    serviceType === messagingProviders.mailgun;

  const SMSProvider = serviceType === messagingProviders.twilio_text;

  const initialValues = {
    email: "",
    phone: "",
  };

  const handleTestConnection = async (value: {
    email: string;
    phone: string;
  }) => {
    const result = await createTestConnectionMessage({
      service_type: serviceType,
      details: {
        to_identity: {
          email: value.email,
          phone_number: value.phone,
        },
      },
    });

    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      toast(successToastParams("Test message successfully sent."));
      if (onClose) {
        onClose();
      }
    }
  };

  return (
    <>
      {!isModal && <Divider mt={10} />}
      {!isModal && (
        <Heading fontSize="md" fontWeight="semibold" mt={10} mb={5}>
          Test connection
        </Heading>
      )}
      <Stack>
        <Formik initialValues={initialValues} onSubmit={handleTestConnection}>
          {({ isSubmitting }) => (
            <Form>
              {emailProvider && (
                <CustomTextInput
                  name="email"
                  label="Email"
                  placeholder="youremail@domain.com"
                  isRequired
                />
              )}
              {SMSProvider && (
                <CustomTextInput
                  name="phone"
                  label="Phone"
                  placeholder="+10000000000"
                  isRequired
                />
              )}
              <Box mt={10}>
                <Button htmlType="reset" className="mr-2">
                  Reset
                </Button>
                <Button
                  disabled={isSubmitting}
                  htmlType="submit"
                  type="primary"
                  data-testid="save-btn"
                >
                  Test configuration
                </Button>
              </Box>
            </Form>
          )}
        </Formik>
      </Stack>
    </>
  );
};

export default TestMessagingProviderConnectionButton;
