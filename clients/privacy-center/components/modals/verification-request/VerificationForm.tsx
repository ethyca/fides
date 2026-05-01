import { Button, Flex, Form, Input, Text, Title } from "fidesui";
import React, { useEffect } from "react";

import { ModalViews, VerificationType } from "../types";
import { useVerificationForm } from "./useVerificationForm";

type VerificationFormProps = {
  isOpen: boolean;
  onClose: () => void;
  requestId: string;
  setCurrentView: (view: ModalViews) => void;
  resetView: ModalViews;
  verificationType: VerificationType;
  successHandler: () => void;
  verificationTitle?: string | null;
  verificationDescription?: string | null;
  verificationSubmitButtonText?: string | null;
  verificationResendButtonText?: string | null;
};

const VerificationForm = ({
  isOpen,
  onClose,
  requestId,
  setCurrentView,
  resetView,
  verificationType,
  successHandler,
  verificationTitle,
  verificationDescription,
  verificationSubmitButtonText,
  verificationResendButtonText,
}: VerificationFormProps) => {
  const {
    errors,
    handleBlur,
    handleChange,
    handleSubmit,
    touched,
    values,
    isValid,
    isSubmitting,
    dirty,
    resetForm,
    resetVerificationProcess,
  } = useVerificationForm({
    onClose,
    requestId,
    setCurrentView,
    resetView,
    verificationType,
    successHandler,
  });

  useEffect(() => resetForm(), [isOpen, resetForm]);

  return (
    <Flex gap="medium" vertical>
      {verificationTitle && (
        <Title level={4} style={{ margin: 0 }}>
          {verificationTitle}
        </Title>
      )}
      <Text type="secondary">
        {verificationDescription ??
          "A verification code has been sent. Return to this window and enter the code below."}
      </Text>
      <Form
        onFinish={handleSubmit}
        data-testid="verification-form"
        layout="vertical"
      >
        <Form.Item
          required
          validateStatus={touched.code && !!errors.code ? "error" : undefined}
          label="Verification code"
          help={touched.code && errors.code}
          hasFeedback={touched.code && !!errors.code}
        >
          <Input
            id="code"
            placeholder="Verification code"
            onChange={handleChange}
            onBlur={handleBlur}
            value={values.code}
          />
        </Form.Item>
        <Flex justify="stretch" gap="medium">
          <Button variant="outlined" onClick={resetVerificationProcess} block>
            {verificationResendButtonText ?? "Resend code"}
          </Button>
          <Button
            htmlType="submit"
            type="primary"
            loading={isSubmitting}
            disabled={isSubmitting || !(isValid && dirty)}
            block
          >
            {verificationSubmitButtonText ?? "Submit code"}
          </Button>
        </Flex>
      </Form>
    </Flex>
  );
};

export default VerificationForm;
