import { Button, Flex, Form, Input, Modal } from "fidesui";
import React, { useCallback, useEffect, useState } from "react";

type DenyModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onDenyRequest: (reason: string) => Promise<any>;
};

const initialValues = { denialReason: "" };
type FormValues = typeof initialValues;

const DenyPrivacyRequestModal = ({
  isOpen,
  onClose,
  onDenyRequest,
}: DenyModalProps) => {
  const [form] = Form.useForm<FormValues>();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const allValues = Form.useWatch([], form);
  const [isDirty, setIsDirty] = useState(false);
  const [isFormValid, setIsFormValid] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      form.resetFields();
      setIsDirty(false);
      setIsFormValid(false);
    }
  }, [isOpen, form]);

  useEffect(() => {
    const touched = form.isFieldsTouched();
    setIsDirty(touched);
  }, [allValues, form]);

  useEffect(() => {
    form
      .validateFields({ validateOnly: true })
      .then(() => setIsFormValid(true))
      .catch(() => setIsFormValid(false));
  }, [allValues, form]);

  const handleFinish = useCallback(
    async (values: FormValues) => {
      setIsSubmitting(true);
      try {
        await onDenyRequest(values.denialReason);
        onClose();
      } finally {
        setIsSubmitting(false);
      }
    },
    [onDenyRequest, onClose],
  );

  return (
    <Modal
      open={isOpen}
      onCancel={onClose}
      centered
      destroyOnHidden
      data-testid="deny-privacy-request-modal"
      title="Privacy request denial"
      footer={null}
    >
      <Form form={form} initialValues={initialValues} onFinish={handleFinish}>
        <div className="mb-2 text-sm text-gray-500">
          Please enter a reason for denying this privacy request. Please note:
          this can be seen by the user in their notification email.
        </div>
        <Form.Item
          name="denialReason"
          rules={[{ required: true, message: "Reason for denial is required" }]}
        >
          <Input.TextArea rows={4} data-testid="input-denialReason" />
        </Form.Item>

        <Flex justify="flex-end" className="mt-4" gap="small">
          <Button disabled={isSubmitting} onClick={onClose}>
            Cancel
          </Button>
          <Button
            htmlType="submit"
            type="primary"
            disabled={!isDirty || !isFormValid}
            loading={isSubmitting}
            data-testid="deny-privacy-request-modal-btn"
          >
            Confirm
          </Button>
        </Flex>
      </Form>
    </Modal>
  );
};

export default DenyPrivacyRequestModal;
