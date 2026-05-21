import { Button, Flex, Form, Input, Text, UploadFile } from "fidesui";
import React from "react";

import { isFieldVisible } from "~/common/visibility";
import CustomFieldRenderer, {
  CustomFieldRendererProps,
} from "~/components/common/CustomFieldRenderer";
import { ModalViews } from "~/components/modals/types";
import { PhoneInput } from "~/components/phone-input";
import { CustomConfigField, PrivacyRequestOption } from "~/types/config";
import { FormFieldValue } from "~/types/forms";

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

  const buildCustomFieldProps = (
    key: string,
    value: FormFieldValue,
    fieldConfig: CustomConfigField,
  ): CustomFieldRendererProps => {
    const sharedProps = {
      fieldKey: key,
      onBlur: () => handleBlur({ target: { name: key } }),
      error: touched[key] && errors[key] ? (errors[key] as string) : undefined,
    };
    switch (fieldConfig.field_type) {
      case "multiselect":
      case "checkbox_group": {
        let arrayValue: string[];
        if (typeof value === "string") {
          arrayValue = [value];
        } else if (Array.isArray(value)) {
          arrayValue = value as string[];
        } else {
          arrayValue = [];
        }
        return {
          ...fieldConfig,
          ...sharedProps,
          value: arrayValue,
          onChange: (v: Array<string>) => setFieldValue(key, v),
        };
      }
      case "checkbox":
        return {
          ...fieldConfig,
          ...sharedProps,
          value: Boolean(value),
          onChange: (v: boolean) => setFieldValue(key, v),
        };
      case "file":
        return {
          ...fieldConfig,
          ...sharedProps,
          value: Array.isArray(value) ? (value as UploadFile[]) : [],
          onChange: (fileList: UploadFile[]) => setFieldValue(key, fileList),
        };
      default: {
        let stringValue: string;
        if (typeof value === "string") {
          stringValue = value;
        } else if (Array.isArray(value) && value.length > 0) {
          stringValue = value[0] as string;
        } else {
          stringValue = "";
        }
        return {
          ...fieldConfig,
          ...sharedProps,
          value: stringValue,
          onChange: (v: string) => setFieldValue(key, v),
        };
      }
    }
  };

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
    // custom + custom-identity render via the same CustomFieldRenderer pipeline
    // they always have. The hidden / visible_when filters apply only to those —
    // legacy identity fields above don't honor those props in the existing UX.
    const { key, field: item } = field;
    if (!item) {
      return null;
    }
    if (item.hidden || !isFieldVisible(item, values)) {
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
          {...buildCustomFieldProps(key, values[key], item)}
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
