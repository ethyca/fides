import {
  AntButton as Button,
  AntFlex as Flex,
  AntForm as Form,
  AntInput as Input,
  AntText as Text,
} from "fidesui";
import React, { useEffect } from "react";

import CustomFieldRenderer, {
  CustomFieldRendererProps,
} from "~/components/common/CustomFieldRenderer";
import { ModalViews } from "~/components/modals/types";
import { PhoneInput } from "~/components/phone-input";
import { useConfig } from "~/features/common/config.slice";
import { CustomConfigField } from "~/types/config";

import useConsentRequestForm from "./useConsentReuestForm";

type ConsentRequestFormProps = {
  isOpen: boolean;
  onClose: () => void;
  setCurrentView: (view: ModalViews) => void;
  setConsentRequestId: (id: string) => void;
  isVerificationRequired: boolean;
  successHandler: () => void;
};

const ConsentRequestForm = ({
  isOpen,
  onClose,
  setCurrentView,
  setConsentRequestId,
  isVerificationRequired,
  successHandler,
}: ConsentRequestFormProps) => {
  const {
    errors,
    handleBlur,
    handleChange,
    handleSubmit,
    touched,
    values,
    isSubmitting,
    setFieldValue,
    resetForm,
    identityInputs: { email: emailInput, phone: phoneInput },
    customPrivacyRequestFields,
  } = useConsentRequestForm({
    onClose,
    setCurrentView,
    setConsentRequestId,
    isVerificationRequired,
    successHandler,
  });

  const config = useConfig();

  useEffect(() => resetForm(), [isOpen, resetForm]);

  return (
    <Form onFinish={handleSubmit} data-testid="consent-request-form">
      <Text>{config.consent?.button.description}</Text>
      {config.consent?.button.description_subtext?.map((paragraph) => (
        <Text key={paragraph}>{paragraph}</Text>
      ))}
      {isVerificationRequired ? (
        <Text>We will send you a verification code.</Text>
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
      {phoneInput === "required" ? (
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
      {Object.entries(customPrivacyRequestFields).map(([key, item]) => {
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

        return (
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
        );
      })}
      <Form.Item>
        <Flex justify="space-between" gap="middle">
          <Button type="default" variant="outlined" onClick={onClose} block>
            {config.consent?.button.cancelButtonText || "Cancel"}
          </Button>
          <Button
            htmlType="submit"
            type="primary"
            loading={isSubmitting}
            disabled={isSubmitting}
            block
          >
            {config.consent?.button.confirmButtonText || "Continue"}
          </Button>
        </Flex>
      </Form.Item>
    </Form>
  );
};

export default ConsentRequestForm;
