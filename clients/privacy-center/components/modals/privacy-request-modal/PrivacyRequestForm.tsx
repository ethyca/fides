import {
  AntButton as Button,
  AntFlex as Flex,
  AntForm as Form,
  AntInput as Input,
  AntText as Text,
} from "fidesui";
import React from "react";

import CustomFieldRenderer, {
  CustomFieldRendererProps,
} from "~/components/common/CustomFieldRenderer";
import { ModalViews } from "~/components/modals/types";
import { PhoneInput } from "~/components/phone-input";
import { useConfig } from "~/features/common/config.slice";
import { CustomConfigField, PrivacyRequestOption } from "~/types/config";

import usePrivacyRequestForm from "./usePrivacyRequestForm";

type PrivacyRequestFormProps = {
  onClose: () => void;
  openAction: number | null;
  setCurrentView: (view: ModalViews) => void;
  setPrivacyRequestId: (id: string) => void;
  isVerificationRequired: boolean;
};

const PrivacyRequestForm = ({
  onClose,
  openAction,
  setCurrentView,
  setPrivacyRequestId,
  isVerificationRequired,
}: PrivacyRequestFormProps) => {
  const config = useConfig();

  const action =
    typeof openAction === "number"
      ? (config.actions[openAction] as PrivacyRequestOption)
      : undefined;

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
    onClose,
    action,
    setCurrentView,
    setPrivacyRequestId,
    isVerificationRequired,
  });

  if (!action) {
    return null;
  }

  return (
    <Flex vertical gap="middle">
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
            help={touched.name && errors.name}
            required={nameInput === "required"}
            hasFeedback={touched.name && !!errors.name}
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
            help={touched.email && errors.email}
            required={emailInput === "required"}
            hasFeedback={touched.email && !!errors.email}
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
            help={touched.phone && errors.phone}
            required={phoneInput === "required"}
            hasFeedback={touched.phone && !!errors.phone}
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
              value: string | string[],
              fieldConfig: CustomConfigField,
            ): CustomFieldRendererProps => {
              const sharedProps = {
                fieldKey: key,
                onBlur: () => handleBlur({ target: { name: key } }),
                error: touched[key] && errors[key] ? errors[key] : undefined,
              };

              switch (fieldConfig.field_type) {
                case "multiselect":
                  return {
                    ...fieldConfig,
                    ...sharedProps,
                    value: typeof value === "string" ? [value] : value,
                    onChange: (v: Array<string>) => {
                      setFieldValue(key, v);
                    },
                  };
                default:
                  return {
                    ...fieldConfig,
                    ...sharedProps,
                    value: typeof value === "string" ? value : value?.[0],
                    onChange: (v: string) => {
                      setFieldValue(key, v);
                    },
                  };
              }
            };

            return item ? (
              <Form.Item
                key={key}
                id={key}
                validateStatus={
                  touched[key] && !!errors[key] ? "error" : undefined
                }
                help={touched[key] && errors[key]}
                required={item.required !== false}
                hasFeedback={
                  item.field_type === "text" && touched[key] && !!errors[key]
                }
                label={item.label}
                htmlFor={key}
              >
                <CustomFieldRenderer {...customFieldProps(values[key], item)} />
              </Form.Item>
            ) : null;
          })}
        <Flex justify="stretch" gap="middle">
          <Button type="default" variant="outlined" onClick={onClose} block>
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
