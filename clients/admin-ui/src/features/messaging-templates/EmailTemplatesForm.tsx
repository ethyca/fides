import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import { Button, Card, Flex, Form, Input, useMessage } from "fidesui";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";

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
  const message = useMessage();
  const [form] = Form.useForm<EmailTemplatesFormValues>();

  const initialValues = emailTemplates.reduce(
    (acc, template) => ({
      ...acc,
      [template.type]: { label: template.label, content: template.content },
    }),
    {} as EmailTemplatesFormValues,
  );

  const handleSubmit = async (values: EmailTemplatesFormValues) => {
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
        message.error(errorMsg);
      } else {
        message.success("Email templates saved.");
        // Re-baseline the form: resetFields() clears antd's touched flags (but
        // reverts to the original initialValues), then setFieldsValue re-applies
        // the just-saved data on top. Together they make the saved values the
        // new baseline so Save becomes disabled until the next edit.
        form.resetFields();
        form.setFieldsValue(values);
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

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={initialValues}
      onFinish={handleSubmit}
      className="py-3"
    >
      {Object.entries(initialValues).map(([key, value]) => (
        <Card key={key} title={value.label} className="my-3">
          <Form.Item
            name={[key, "content", "subject"]}
            label="Message subject"
            rules={[{ required: true, message: "Subject is required" }]}
          >
            <Input data-testid={`input-${key}.content.subject`} />
          </Form.Item>
          <Form.Item
            name={[key, "content", "body"]}
            label="Message body"
            rules={[{ required: true, message: "Body is required" }]}
          >
            <Input.TextArea
              autoSize={{ minRows: 3 }}
              data-testid={`input-${key}.content.body`}
            />
          </Form.Item>
        </Card>
      ))}
      <Flex justify="flex-end" className="w-full pt-2">
        <Form.Item shouldUpdate noStyle>
          {() => (
            <Button
              htmlType="submit"
              type="primary"
              disabled={
                !form.isFieldsTouched() ||
                form.getFieldsError().some(({ errors }) => errors.length > 0)
              }
              loading={isLoading}
              data-testid="submit-btn"
            >
              Save
            </Button>
          )}
        </Form.Item>
      </Flex>
    </Form>
  );
};

export default EmailTemplatesForm;
