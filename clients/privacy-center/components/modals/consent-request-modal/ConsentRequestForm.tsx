import { Button, Flex, Form, Input, Text, UploadFile } from "fidesui";
import React, { useEffect } from "react";

import CustomFieldRenderer, {
  CustomFieldRendererProps,
} from "~/components/common/CustomFieldRenderer";
import { ModalViews } from "~/components/modals/types";
import { PhoneInput } from "~/components/phone-input";
import { useConfig } from "~/features/common/config.slice";
import { CustomConfigField } from "~/types/config";
import { FormFieldValue } from "~/types/forms";

import useConsentRequestForm from "./useConsentRequestForm";

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
    <Flex vertical gap="medium">
      <Text>{config.consent?.button.description}</Text>
      {config.consent?.button.description_subtext?.map((paragraph) => (
        <Text key={paragraph}>{paragraph}</Text>
      ))}
      {isVerificationRequired ? (
        <Text>We will send you a verification code.</Text>
      ) : null}

      <Form
        onFinish={handleSubmit}
        layout="vertical"
        data-testid="consent-request-form"
      >
        {!!emailInput && (
          <Form.Item
            validateStatus={
              touched.email && !!errors.email ? "error" : undefined
            }
            help={touched.email && (errors.email as string)}
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
              touched.phone && !!errors.phone ? "error" : undefined
            }
            help={touched.phone && (errors.phone as string)}
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
        {Object.entries(customPrivacyRequestFields).map(([key, item]) => {
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

          return (
            <Form.Item
              key={key}
              id={key}
              validateStatus={
                touched[key] && Boolean(errors[key]) ? "error" : undefined
              }
              help={touched[key] && (errors[key] as string)}
              required={item.required !== false}
              hasFeedback={
                item.field_type === "text" && touched[key] && !!errors[key]
              }
              label={item.label}
              htmlFor={key}
            >
              <CustomFieldRenderer {...customFieldProps(values[key], item)} />
            </Form.Item>
          );
        })}
        <Flex justify="stretch" gap="medium">
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
      </Form>
    </Flex>
  );
};

export default ConsentRequestForm;
