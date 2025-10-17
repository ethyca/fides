import type { ModalStaticFunctions } from "antd/es/modal/confirm";
import {
  AntFlex as Flex,
  AntForm as Form,
  AntFormInstance as FormInstance,
  AntInput as Input,
  AntParagraph as Paragraph,
} from "fidesui";
import React from "react";

const DenyRequestForm = ({ form }: { form: FormInstance }) => {
  return (
    <Flex vertical gap={4}>
      <Paragraph>
        Please enter a reason for denying this privacy request. Please note:
        this can be seen by the user in their notification email.
      </Paragraph>
      <Form form={form} layout="vertical">
        <Form.Item
          name="denialReason"
          rules={[
            {
              required: true,
              message: "Please enter a reason for denial",
            },
          ]}
        >
          <Input.TextArea placeholder="Enter reason for denial..." rows={4} />
        </Form.Item>
      </Form>
    </Flex>
  );
};

export const useDenyPrivacyRequestModal = (modalApi: ModalStaticFunctions) => {
  const [form] = Form.useForm();

  const openDenyPrivacyRequestModal = React.useCallback(
    () =>
      new Promise<string | null>((resolve) => {
        modalApi.confirm({
          title: "Privacy request denial",
          content: <DenyRequestForm form={form} />,
          okText: "Confirm",
          cancelText: "Cancel",
          onOk: (closeModal) => {
            form
              .validateFields()
              .then((values) => {
                // if validation passes, close modal, reset form, and resolve with the denial reason.
                closeModal(values);
                form.resetFields();
                resolve(values.denialReason);
              })
              .catch(() => {
                // form validation is expected if form isn't filled. safe to ignore.
              });
          },
          onCancel: () => {
            // if modal is cancelled, resolve with null.
            form.resetFields();
            resolve(null);
          },
          width: 500,
          centered: true,
          open: true,
        });
      }),
    [modalApi, form],
  );
  return { openDenyPrivacyRequestModal };
};
