import { Alert, Button, Flex, Form, Input, Text } from "fidesui";
import React from "react";

import { buildCustomFieldProps } from "~/components/common/buildCustomFieldProps";
import CustomFieldRenderer from "~/components/common/CustomFieldRenderer";
import { ModalViews } from "~/components/modals/types";
import { PhoneInput } from "~/components/phone-input";
import { PrivacyRequestOption } from "~/types/config";

import usePrivacyRequestForm, { OrderedField } from "./usePrivacyRequestForm";

type PrivacyRequestFormProps = {
  onExit: () => void;
  openAction: PrivacyRequestOption | undefined;
  setCurrentView: (view: ModalViews) => void;
  setPrivacyRequestId: (id: string) => void;
  isVerificationRequired: boolean;
  onSuccessWithoutVerification?: () => void;
};

const PrivacyRequestForm = ({
  onExit,
  openAction,
  setCurrentView,
  setPrivacyRequestId,
  isVerificationRequired,
  onSuccessWithoutVerification,
}: PrivacyRequestFormProps) => {
  const action = openAction;

  const {
    errors,
    handleBlur,
    handleChange,
    handleSubmit,
    setFieldValue,
    touched,
    values,
    isSubmitting,
    orderedFields,
    applicableFields,
    validationError,
  } = usePrivacyRequestForm({
    onExit,
    action,
    setCurrentView,
    setPrivacyRequestId,
    isVerificationRequired,
    onSuccessWithoutVerification,
  });

  if (!action) {
    return null;
  }

  const formContext = { setFieldValue, handleBlur, touched, errors };

  const renderField = (field: OrderedField): React.ReactElement | null => {
    if (field.kind === "name") {
      return (
        <Form.Item
          key="name"
          validateStatus={
            touched.name && Boolean(errors.name) ? "error" : undefined
          }
          help={touched.name && (errors.name as string)}
          required={field.mode === "required"}
          label="Name"
          htmlFor="name"
        >
          <Input
            id="name"
            name="name"
            placeholder="Michael Brown"
            onChange={handleChange}
            onBlur={handleBlur}
            value={values.name}
          />
        </Form.Item>
      );
    }
    if (field.kind === "email") {
      return (
        <Form.Item
          key="email"
          validateStatus={
            touched.email && Boolean(errors.email) ? "error" : undefined
          }
          help={touched.email && (errors.email as string)}
          required={field.mode === "required"}
          label="Email"
          htmlFor="email"
        >
          <Input
            id="email"
            name="email"
            type="email"
            placeholder="your-email@example.com"
            onChange={handleChange}
            onBlur={handleBlur}
            value={values.email}
          />
        </Form.Item>
      );
    }
    if (field.kind === "phone") {
      return (
        <Form.Item
          key="phone"
          validateStatus={
            touched.phone && Boolean(errors.phone) ? "error" : undefined
          }
          help={touched.phone && (errors.phone as string)}
          required={field.mode === "required"}
          label="Phone"
          htmlFor="phone"
        >
          <PhoneInput
            id="phone"
            name="phone"
            onChange={(value) => setFieldValue("phone", value, true)}
            onBlur={handleBlur}
            value={values.phone}
          />
        </Form.Item>
      );
    }
    if (field.kind !== "custom" && field.kind !== "custom-identity") {
      return null;
    }
    // custom + custom-identity render via the same CustomFieldRenderer pipeline.
    // Hidden fields and fields gated off by display_condition are filtered out.
    // Custom identity fields bypass applicableFields (they don't have display_condition).
    const { key, field: item } = field;
    if (!item) {
      return null;
    }
    if (item.hidden) {
      return null;
    }
    if (field.kind === "custom" && !applicableFields.has(key)) {
      return null;
    }
    const isCheckbox = item.field_type === "checkbox";
    return (
      <Form.Item
        key={key}
        id={key}
        validateStatus={touched[key] && !!errors[key] ? "error" : undefined}
        help={touched[key] && (errors[key] as string)}
        required={item.required !== false}
        label={isCheckbox ? undefined : item.label}
        htmlFor={key}
      >
        <CustomFieldRenderer
          {...buildCustomFieldProps(key, values[key], item, formContext)}
        />
      </Form.Item>
    );
  };

  return (
    <Flex vertical gap="medium">
      <Text type="secondary">{action.description}</Text>
      <Form
        onFinish={handleSubmit}
        data-testid="privacy-request-form"
        layout="vertical"
      >
        {action.description_subtext?.map((paragraph) => (
          <Form.Item key={paragraph}>
            <Text size="sm">{paragraph}</Text>
          </Form.Item>
        ))}
        {validationError && (
          <Alert
            type="error"
            title="Something went wrong. Please try again later."
            showIcon
          />
        )}
        {orderedFields.map(renderField)}
        <Flex justify="stretch" gap="medium">
          <Button type="default" variant="outlined" onClick={onExit} block>
            {action.cancelButtonText || "Cancel"}
          </Button>
          <Button
            htmlType="submit"
            type="primary"
            loading={isSubmitting}
            disabled={isSubmitting}
            block
          >
            {action.confirmButtonText || "Continue"}
          </Button>
        </Flex>
      </Form>
    </Flex>
  );
};

export default PrivacyRequestForm;
