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
    identityInputs: { name: nameInput, email: emailInput, phone: phoneInput },
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
    <Form
      onFinish={handleSubmit}
      data-testid="privacy-request-form"
      layout="vertical"
    >
      <Form.Item>
        <Text>{action.description}</Text>
      </Form.Item>
      {action.description_subtext?.map((paragraph) => (
        <Form.Item key={paragraph}>
          <Text size="sm">{paragraph}</Text>
        </Form.Item>
      ))}
      {nameInput ? (
        <Form.Item
          id="name"
          validateStatus={
            touched.name && Boolean(errors.name) ? "error" : undefined
          }
          help={touched.name && errors.name}
          required={nameInput === "required"}
          label="Name"
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
      ) : null}
      {emailInput ? (
        <Form.Item
          id="email"
          validateStatus={
            touched.email && Boolean(errors.email) ? "error" : undefined
          }
          help={touched.email && errors.email}
          required={emailInput === "required"}
          label="Email"
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
      ) : null}
      {phoneInput ? (
        <Form.Item
          id="phone"
          validateStatus={
            touched.phone && Boolean(errors.phone) ? "error" : undefined
          }
          help={touched.phone && errors.phone}
          required={phoneInput === "required"}
          label="Phone"
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
      ) : null}
      {Object.entries(customPrivacyRequestFields)
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
                touched[key] && Boolean(errors[key]) ? "error" : undefined
              }
              help={touched[key] && errors[key]}
              required={item.required !== false}
              label={item.label}
            >
              <CustomFieldRenderer {...customFieldProps(values[key], item)} />
            </Form.Item>
          ) : null;
        })}
      <Form.Item>
        <Flex justify="space-between" gap="middle">
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
      </Form.Item>
    </Form>
  );
};

export default PrivacyRequestForm;
