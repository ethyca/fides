import { Button, Flex, Form, Input, Text, UploadFile } from "fidesui";
import React from "react";

import CustomFieldRenderer, {
  CustomFieldRendererProps,
} from "~/components/common/CustomFieldRenderer";
import { ModalViews } from "~/components/modals/types";
import { PhoneInput } from "~/components/phone-input";
import { CustomConfigField, PrivacyRequestOption } from "~/types/config";
import { FormFieldValue } from "~/types/forms";

import usePrivacyRequestForm from "./usePrivacyRequestForm";

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
    legacyIdentityFields: {
      name: nameInput,
      email: emailInput,
      phone: phoneInput,
    },
    customIdentityFields,
    customPrivacyRequestFields,
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
        {!!nameInput && (
          <Form.Item
            validateStatus={
              touched.name && Boolean(errors.name) ? "error" : undefined
            }
            help={touched.name && (errors.name as string)}
            required={nameInput === "required"}
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
        )}
        {!!emailInput && (
          <Form.Item
            validateStatus={
              touched.email && Boolean(errors.email) ? "error" : undefined
            }
            help={touched.email && (errors.email as string)}
            required={emailInput === "required"}
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
        )}
        {!!phoneInput && (
          <Form.Item
            validateStatus={
              touched.phone && Boolean(errors.phone) ? "error" : undefined
            }
            help={touched.phone && (errors.phone as string)}
            required={phoneInput === "required"}
            label="Phone"
            htmlFor="phone"
          >
            <PhoneInput
              id="phone"
              name="phone"
              onChange={(value) => {
                setFieldValue("phone", value, true);
              }}
              onBlur={handleBlur}
              value={values.phone}
            />
          </Form.Item>
        )}
        {Object.entries({
          ...customIdentityFields,
          ...customPrivacyRequestFields,
        })
          .filter(([, field]) => !field?.hidden)
          .map(([key, item]) => {
            const customFieldProps = (
              value: FormFieldValue,
              fieldConfig: CustomConfigField,
            ): CustomFieldRendererProps => {
              const sharedProps = {
                fieldKey: key,
                onBlur: () => handleBlur({ target: { name: key } }),
                error:
                  touched[key] && errors[key]
                    ? (errors[key] as string)
                    : undefined,
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
                    onChange: (v: Array<string>) => {
                      setFieldValue(key, v);
                    },
                  };
                }
                case "checkbox":
                  return {
                    ...fieldConfig,
                    ...sharedProps,
                    value: Boolean(value),
                    onChange: (v: boolean) => {
                      setFieldValue(key, v);
                    },
                  };
                case "file":
                  return {
                    ...fieldConfig,
                    ...sharedProps,
                    value: Array.isArray(value) ? (value as UploadFile[]) : [],
                    onChange: (fileList: UploadFile[]) => {
                      setFieldValue(key, fileList);
                    },
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
                    onChange: (v: string) => {
                      setFieldValue(key, v);
                    },
                  };
                }
              }
            };

            const isCheckbox = item?.field_type === "checkbox";

            return item ? (
              <Form.Item
                key={key}
                id={key}
                validateStatus={
                  touched[key] && !!errors[key] ? "error" : undefined
                }
                help={touched[key] && (errors[key] as string)}
                required={item.required !== false}
                label={isCheckbox ? undefined : item.label}
                htmlFor={key}
              >
                <CustomFieldRenderer {...customFieldProps(values[key], item)} />
              </Form.Item>
            ) : null;
          })}
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
