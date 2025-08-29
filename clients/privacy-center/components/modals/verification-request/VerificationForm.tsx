import {
  AntButton as Button,
  AntFlex as Flex,
  AntForm as Form,
  AntInput as Input,
  AntText as Text,
} from "fidesui";
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
};

const VerificationForm = ({
  isOpen,
  onClose,
  requestId,
  setCurrentView,
  resetView,
  verificationType,
  successHandler,
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
    <Flex gap="small" vertical>
      <Text type="secondary">
        A verification code has been sent. Return to this window and enter the
        code below.
      </Text>
      <Form
        onFinish={handleSubmit}
        data-testid="verification-form"
        layout="vertical"
      >
        <Form.Item
          required
          validateStatus={touched.code && !!errors.code ? "error" : undefined}
          label="Verification Code"
          help={touched.code && errors.code}
          hasFeedback={touched.code && !!errors.code}
        >
          <Input
            id="code"
            placeholder="Verification Code"
            onChange={handleChange}
            onBlur={handleBlur}
            value={values.code}
          />
        </Form.Item>
        <Flex vertical gap="middle">
          <Button
            htmlType="submit"
            type="primary"
            loading={isSubmitting}
            disabled={isSubmitting || !(isValid && dirty)}
          >
            Submit code
          </Button>
          <Flex align="center" gap="small" vertical>
            <Text size="sm" type="secondary">
              {`Didn't receive a code?`}
            </Text>
            <Button
              size="small"
              variant="outlined"
              onClick={resetVerificationProcess}
            >
              Click here to try again
            </Button>
          </Flex>
        </Flex>
      </Form>
    </Flex>
  );
};

export default VerificationForm;
