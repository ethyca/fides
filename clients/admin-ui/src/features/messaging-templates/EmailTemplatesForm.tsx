import { Box, Button, Flex, useToast } from "@fidesui/react";
import { Form, Formik, FormikHelpers } from "formik";
import FormSection from "~/features/common/form/FormSection";
import { CustomTextInput } from "~/features/common/form/inputs";
import { useUpdateMessagingTemplatesMutation } from "./messaging-templates.slice";
import { MessagingTemplate } from "./messaging-templates.slice";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import { isErrorResult, getErrorMessage } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";

interface EmailTemplatesFormProps {
  emailTemplates: MessagingTemplate[];
}

type EmailTemplatesFormValues = Record<
  string,
  {
    label: string;
    content: {
      subject: string;
      body: string;
    };
  }
>;

export const EmailTemplatesForm = ({
  emailTemplates,
}: EmailTemplatesFormProps) => {
  const [updateMessagingTemplates, { isLoading }] =
    useUpdateMessagingTemplatesMutation();
  const toast = useToast();

  const handleSubmit = async (
    values: EmailTemplatesFormValues,
    formikHelpers: FormikHelpers<EmailTemplatesFormValues>
  ) => {
    const handleResult = (
      result: { data: {} } | { error: FetchBaseQueryError | SerializedError }
    ) => {
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          "An unexpected error occurred while editing the email templates. Please try again."
        );
        toast(errorToastParams(errorMsg));
      } else {
        toast(successToastParams("Email templates saved."));
        formikHelpers.resetForm({ values });
      }
    };

    // Transform the values object back into an array of MessagingTemplates
    const messagingTemplates = Object.entries(values).map(
      ([key, { label, content }]) => ({
        key,
        label,
        content,
      })
    ) as MessagingTemplate[];

    const result = await updateMessagingTemplates(messagingTemplates);
    handleResult(result);
  };

  const initialValues = emailTemplates.reduce((acc, template) => {
    acc[template.key] = { label: template.label, content: template.content };
    return acc;
  }, {} as EmailTemplatesFormValues);

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      onSubmit={handleSubmit}
    >
      {() => (
        <Form
          style={{
            paddingTop: "12px",
            paddingBottom: "12px",
          }}
        >
          {Object.entries(initialValues).map(([key, value], index) => (
            <Box key={index} py={3}>
              <FormSection title={value.label}>
                <CustomTextInput
                  label="Message subject"
                  name={`${key}.content.subject`}
                  variant="stacked"
                />
                <CustomTextInput
                  label="Message body"
                  name={`${key}.content.body`}
                  type="textarea"
                  variant="stacked"
                />
              </FormSection>
            </Box>
          ))}
          <Flex justifyContent="right" width="100%" paddingTop={2}>
            <Button
              size="sm"
              type="submit"
              colorScheme="primary"
              isLoading={isLoading}
            >
              Save
            </Button>
          </Flex>
        </Form>
      )}
    </Formik>
  );
};

export default EmailTemplatesForm;
