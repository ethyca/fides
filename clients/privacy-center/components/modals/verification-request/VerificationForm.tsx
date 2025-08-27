import {
  AntButton as Button,
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
    <>
      <Text>Enter verification code</Text>
      <Form onFinish={handleSubmit} data-testid="verification-form">
        <Text>
          A verification code has been sent. Return to this window and enter the
          code below.
        </Text>
        <Form.Item
          required
          status={touched.code && Boolean(errors.code) ? "error" : undefined}
          help={errors.code}
        >
          <Input
            id="code"
            placeholder="Verification Code"
            onChange={handleChange}
            onBlur={handleBlur}
            value={values.code}
          />
        </Form.Item>
        <Form.Item>
          <Button
            htmlType="submit"
            type="primary"
            loading={isSubmitting}
            disabled={isSubmitting || !(isValid && dirty)}
          >
            Submit code
          </Button>
          <Text size="sm" type="secondary">
            Didn&apos;t receive a code?
          </Text>{" "}
          <Button
            size="small"
            variant="text"
            onClick={resetVerificationProcess}
          >
            Click here to try again
          </Button>
        </Form.Item>
      </Form>
    </>
  );
};

export default VerificationForm;
