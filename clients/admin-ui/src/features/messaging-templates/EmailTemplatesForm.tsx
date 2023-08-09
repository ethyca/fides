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

export const EmailTemplatesForm = ({
  emailTemplates,
}: EmailTemplatesFormProps) => {
  const [updateMessagingTemplates, { isLoading }] =
    useUpdateMessagingTemplatesMutation();
  const toast = useToast();

  const handleSubmit = async (
    values: Record<string, { subject: string; body: string }>,
    formikHelpers: FormikHelpers<
      Record<string, { subject: string; body: string }>
    >
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
    const messagingTemplates = Object.entries(values).map(([key, content]) => ({
      key,
      content,
    })) as MessagingTemplate[];

    const result = await updateMessagingTemplates(messagingTemplates);
    handleResult(result);
  };

  const initialValues = emailTemplates.reduce((acc, template) => {
    acc[template.key] = template.content;
    return acc;
  }, {} as Record<string, { subject: string; body: string }>);

  function toTitleCase(str: string) {
    return str
      .replace(/_/g, " ")
      .toLowerCase()
      .replace(/^\w/, (char) => char.toUpperCase());
  }

  return (
    <Formik initialValues={initialValues} onSubmit={handleSubmit}>
      {() => (
        <Form
          style={{
            paddingTop: "12px",
            paddingBottom: "12px",
          }}
        >
          {Object.entries(initialValues).map(([key], index) => (
            <Box key={index} py={3}>
              <FormSection title={toTitleCase(key)}>
                <CustomTextInput
                  label="Message subject"
                  name={`${key}.subject`}
                  variant="stacked"
                />
                <CustomTextInput
                  label="Message body"
                  name={`${key}.body`}
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
