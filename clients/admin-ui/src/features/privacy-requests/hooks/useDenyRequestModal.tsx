import type { ModalStaticFunctions } from "antd/es/modal/confirm";
import { CustomTextArea } from "common/form/inputs";
import { AntForm as Form } from "fidesui";
import React from "react";

// Component to handle the form logic
const DenyRequestForm = ({
  onFinish,
}: {
  onFinish: (reason: string) => void;
}) => {
  const [form] = Form.useForm();

  const handleSubmit = (values: { denialReason: string }) => {
    onFinish(values.denialReason);
  };

  return (
    <div>
      <div style={{ color: "#6B7280", fontSize: "14px", marginBottom: "16px" }}>
        Please enter a reason for denying this privacy request. Please note:
        this can be seen by the user in their notification email.
      </div>
      <Form
        form={form}
        layout="vertical"
        initialValues={{ denialReason: "" }}
        onFinish={handleSubmit}
      >
        <Form.Item
          name="denialReason"
          rules={[
            {
              required: true,
              message: "Please enter a reason for denial",
            },
          ]}
        >
          <CustomTextArea
            name="denialReason"
            textAreaProps={{
              focusBorderColor: "primary.600",
              resize: "none",
              placeholder: "Enter reason for denial...",
            }}
          />
        </Form.Item>
      </Form>
    </div>
  );
};

export const useDenyPrivacyRequestModal = (modalApi: ModalStaticFunctions) => {
  const openDenyPrivacyRequestModal = React.useCallback(
    (onFinish: (reason: string) => void) => {
      modalApi.confirm({
        title: "Privacy request denial",
        content: <DenyRequestForm onFinish={onFinish} />,
        okText: "Confirm",
        cancelText: "Cancel",
        onOk: () => {
          // The form will handle submission through onFinish
          return Promise.resolve();
        },
        width: 456,
        centered: true,
      });
    },
    [modalApi],
  );

  return { openDenyPrivacyRequestModal };
};
