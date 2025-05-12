import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import { AntButton as Button, Box, Flex, useToast } from "fidesui";
import { Form, Formik, FormikHelpers } from "formik";

import FormSection from "~/features/common/form/FormSection";
import { CustomTextArea, CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";

import {
  MessagingTemplate,
  useUpdateMessagingTemplatesMutation,
} from "./messaging-templates.slice";

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

const EmailTemplatesForm = ({ emailTemplates }: EmailTemplatesFormProps) => {
  const [updateMessagingTemplates, { isLoading }] =
    useUpdateMessagingTemplatesMutation();
  const toast = useToast();

  const handleSubmit = async (
    values: EmailTemplatesFormValues,
    formikHelpers: FormikHelpers<EmailTemplatesFormValues>,
  ) => {
    const handleResult = (
      result:
        | { data: object }
        | { error: FetchBaseQueryError | SerializedError },
    ) => {
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          "An unexpected error occurred while editing the email templates. Please try again.",
        );
        toast(errorToastParams(errorMsg));
      } else {
        toast(successToastParams("Email templates saved."));
        formikHelpers.resetForm({ values });
      }
    };

    // Transform the values object back into an array of MessagingTemplates
    const messagingTemplates = Object.entries(values).map(
      ([type, { content }]) => ({
        type,
        content,
      }),
    ) as MessagingTemplate[];

    const result = await updateMessagingTemplates(messagingTemplates);
    handleResult(result);
  };

  const initialValues = emailTemplates.reduce(
    (acc, template) => ({
      ...acc,
      [template.type]: { label: template.label, content: template.content },
    }),
    {} as EmailTemplatesFormValues,
  );

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
          {Object.entries(initialValues).map(([key, value]) => (
            <Box key={key} py={3}>
              <FormSection title={value.label}>
                <CustomTextInput
                  label="Message subject"
                  name={`${key}.content.subject`}
                  variant="stacked"
                />
                <CustomTextArea
                  label="Message body"
                  name={`${key}.content.body`}
                  variant="stacked"
                  resize
                />
              </FormSection>
            </Box>
          ))}
          <Flex justifyContent="right" width="100%" paddingTop={2}>
            <Button htmlType="submit" type="primary" loading={isLoading}>
              Save
            </Button>
          </Flex>
        </Form>
      )}
    </Formik>
  );
};

export default EmailTemplatesForm;
