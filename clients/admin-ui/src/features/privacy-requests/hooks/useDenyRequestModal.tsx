import type { ModalStaticFunctions } from "antd/es/modal/confirm";
import {
  AntFlex as Flex,
  AntForm as Form,
  AntFormInstance as FormInstance,
  AntInput as Input,
  AntParagraph as Paragraph,
  useFormModal,
} from "fidesui";
import React, { useCallback } from "react";

const DenyRequestForm = ({ form }: { form: FormInstance }) => {
  return (
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
  );
};

export const useDenyPrivacyRequestModal = (modalApi: ModalStaticFunctions) => {
  const { openFormModal } = useFormModal<{ denialReason: string }>(modalApi);

  const openDenyPrivacyRequestModal = useCallback(async () => {
    const reason = await openFormModal({
      title: "Privacy request denial",
      content: (form) => (
        <Flex vertical gap={4}>
          <Paragraph>
            Please enter a reason for denying this privacy request. Please note:
            this can be seen by the user in their notification email.
          </Paragraph>
          <DenyRequestForm form={form} />
        </Flex>
      ),
      okText: "Confirm",
      cancelText: "Cancel",
      width: 500,
      centered: true,
    });
    if (!reason) {
      return null;
    }
    return reason?.denialReason;
  }, [openFormModal]);

  return { openDenyPrivacyRequestModal };
};
