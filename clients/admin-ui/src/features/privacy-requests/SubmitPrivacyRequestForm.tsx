import {
  Button,
  Checkbox,
  Flex,
  Form,
  type FormRule,
  Icons,
  Input,
  LocationSelect,
  Select,
  useMessage,
} from "fidesui";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  findActionFromPolicyKey,
  generateFormRulesFromAction,
} from "~/features/privacy-requests/form/helpers";
import { useGetPrivacyCenterConfigQuery } from "~/features/privacy-requests/privacy-requests.slice";
import {
  fides__api__schemas__privacy_center_config__CustomPrivacyRequestField,
  IdentityInputs,
  PrivacyRequestCreateExtended as PrivacyRequestCreate,
  PrivacyRequestOption,
} from "~/types/api";

/**
 * Mirror location type from backend
 */
export type LocationCustomPrivacyRequestField = {
  label: string;
  required?: boolean | null;
  default_value?: string | null;
  hidden?: boolean | null;
  query_param_key?: string | null;
  field_type: "location";
  ip_geolocation_hint?: boolean | null;
};

export type SelectCustomPrivacyRequestField = {
  label: string;
  required?: boolean | null;
  default_value?: string | null;
  hidden?: boolean | null;
  query_param_key?: string | null;
  field_type: "select";
  options: string[];
};

export type PrivacyRequestSubmitFormValues = PrivacyRequestCreate & {
  is_verified: boolean;
};

const defaultInitialValues: PrivacyRequestSubmitFormValues = {
  is_verified: false,
  policy_key: "",
  identity: {},
};

const IdentityFields = ({
  identityInputs,
  rules,
}: {
  identityInputs?: IdentityInputs | null;
  rules: Record<string, FormRule[]>;
}) => {
  if (!identityInputs) {
    return null;
  }
  return (
    <>
      {identityInputs.email ? (
        <Form.Item
          name={["identity", "email"]}
          label="User email address"
          rules={rules["identity.email"]}
          layout="vertical"
        >
          <Input data-testid="input-identity.email" />
        </Form.Item>
      ) : null}
      {identityInputs.phone ? (
        <Form.Item
          name={["identity", "phone_number"]}
          label="User phone number"
          rules={rules["identity.phone_number"]}
          layout="vertical"
        >
          <Input data-testid="input-identity.phone_number" />
        </Form.Item>
      ) : null}
    </>
  );
};

const LocationSelectField = ({
  label,
  name,
  required,
  rules,
}: {
  label: string;
  name: string;
  required: boolean;
  rules?: FormRule[];
}) => {
  return (
    <Form.Item
      label={label}
      name={name}
      required={required}
      rules={rules}
      layout="vertical"
    >
      <LocationSelect />
    </Form.Item>
  );
};

const CustomFields = ({
  customFieldInputs,
  rules,
}: {
  customFieldInputs?: Record<
    string,
    | fides__api__schemas__privacy_center_config__CustomPrivacyRequestField
    | LocationCustomPrivacyRequestField
    | SelectCustomPrivacyRequestField
  > | null;
  rules: Record<string, FormRule[]>;
}) => {
  if (!customFieldInputs) {
    return null;
  }
  const allInputs = Object.entries(customFieldInputs);
  return (
    <>
      {allInputs.map(([fieldName, fieldInfo]) => {
        if (
          "field_type" in fieldInfo &&
          fieldInfo.field_type === "location"
        ) {
          return (
            <LocationSelectField
              name={fieldName}
              key={fieldName}
              label={fieldInfo.label}
              required={Boolean(fieldInfo.required)}
              rules={rules[fieldName]}
            />
          );
        }

        const isSelectField = (
          info: typeof fieldInfo,
        ): info is SelectCustomPrivacyRequestField =>
          "field_type" in info && info.field_type === "select";

        return (
          <div key={fieldName}>
            <Form.Item
              name={["custom_privacy_request_fields", fieldName, "label"]}
              hidden
            >
              <Input />
            </Form.Item>
            <Form.Item
              name={["custom_privacy_request_fields", fieldName, "value"]}
              label={fieldInfo.label}
              required={Boolean(fieldInfo.required)}
              rules={rules[`custom_privacy_request_fields.${fieldName}.value`]}
              layout="vertical"
            >
              {isSelectField(fieldInfo) ? (
                <Select
                  options={fieldInfo.options.map((opt) => ({
                    label: opt,
                    value: opt,
                  }))}
                  data-testid={`input-custom_privacy_request_fields.${fieldName}.value`}
                />
              ) : (
                <Input
                  data-testid={`input-custom_privacy_request_fields.${fieldName}.value`}
                />
              )}
            </Form.Item>
          </div>
        );
      })}
    </>
  );
};

const SubmitPrivacyRequestForm = ({
  onSubmit,
  onCancel,
}: {
  onSubmit: (values: PrivacyRequestSubmitFormValues) => void;
  onCancel: () => void;
}) => {
  const [form] = Form.useForm<PrivacyRequestSubmitFormValues>();
  const { data: config } = useGetPrivacyCenterConfigQuery();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const policyKey = Form.useWatch("policy_key", form);
  const isVerified = Form.useWatch("is_verified", form);

  const currentAction = useMemo(
    () => findActionFromPolicyKey(policyKey ?? "", config?.actions),
    [policyKey, config?.actions],
  );

  const rules = useMemo(
    () => generateFormRulesFromAction(currentAction),
    [currentAction],
  );

  const handleResetCustomFields = useCallback(
    (value: string) => {
      const newAction = findActionFromPolicyKey(value, config?.actions);
      if (!newAction?.custom_privacy_request_fields) {
        form.setFieldValue("custom_privacy_request_fields", undefined);
        return;
      }
      const newCustomFields = Object.entries(
        newAction.custom_privacy_request_fields,
      )
        .map(([fieldName, fieldInfo]) => ({
          [fieldName]: {
            label: fieldInfo.label,
            value: fieldInfo.default_value,
          },
        }))
        .reduce((acc, next) => ({ ...acc, ...next }), {});
      form.setFieldValue("custom_privacy_request_fields", newCustomFields);
    },
    [config?.actions, form],
  );

  // Track dirty state
  const allValues = Form.useWatch([], form);
  const [isDirty, setIsDirty] = useState(false);
  const [isFormValid, setIsFormValid] = useState(false);

  useEffect(() => {
    const touched = form.isFieldsTouched();
    setIsDirty(touched);
  }, [allValues, form]);

  useEffect(() => {
    form
      .validateFields({ validateOnly: true })
      .then(() => setIsFormValid(true))
      .catch(() => setIsFormValid(false));
  }, [allValues, form]);

  const handleFinish = async (values: PrivacyRequestSubmitFormValues) => {
    setIsSubmitting(true);
    try {
      await onSubmit(values);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Form
      form={form}
      initialValues={defaultInitialValues}
      onFinish={handleFinish}
      layout="vertical"
    >
      <Flex vertical className="mb-2">
        <Form.Item
          name="policy_key"
          label="Request type"
          rules={rules.policy_key}
          layout="vertical"
          required
        >
          <Select
            aria-label="Request type"
            options={
              config?.actions.map((action: PrivacyRequestOption) => ({
                label: action.title,
                value: action.policy_key,
              })) ?? []
            }
            onChange={handleResetCustomFields}
            data-testid="controlled-select-policy_key"
          />
        </Form.Item>
        <IdentityFields
          identityInputs={currentAction?.identity_inputs}
          rules={rules}
        />
        <CustomFields
          customFieldInputs={currentAction?.custom_privacy_request_fields}
          rules={rules}
        />
        <Form.Item name="is_verified" valuePropName="checked">
          <Checkbox data-testid="input-is_verified">
            I confirm that I have verified this user information
          </Checkbox>
        </Form.Item>
        <div className="flex gap-4 self-end">
          <Button
            onClick={() => {
              form.resetFields();
              onCancel();
            }}
          >
            Cancel
          </Button>
          <Button
            htmlType="submit"
            type="primary"
            disabled={!isVerified || !isDirty || !isFormValid}
            loading={isSubmitting}
            data-testid="submit-btn"
          >
            Create
          </Button>
        </div>
      </Flex>
    </Form>
  );
};

export const CopyPrivacyRequestLinkForm = ({
  onSubmit,
  onCancel,
  privacyCenterUrl,
}: {
  onSubmit: (values: { identity: { email: string } }) => void;
  onCancel: () => void;
  privacyCenterUrl: string;
}) => {
  const [form] = Form.useForm<{ identity: { email: string } }>();
  const message = useMessage();

  const allValues = Form.useWatch([], form);
  const [isDirty, setIsDirty] = useState(false);
  const [isFormValid, setIsFormValid] = useState(false);

  useEffect(() => {
    const touched = form.isFieldsTouched();
    setIsDirty(touched);
  }, [allValues, form]);

  useEffect(() => {
    form
      .validateFields({ validateOnly: true })
      .then(() => setIsFormValid(true))
      .catch(() => setIsFormValid(false));
  }, [allValues, form]);

  const handleFinish = async (values: { identity: { email: string } }) => {
    const url = `${privacyCenterUrl}?email=${encodeURIComponent(values.identity.email)}`;
    try {
      await navigator.clipboard.writeText(url);
      message.success("DSR Link Copied!");
    } catch {
      message.error("Failed to copy link to clipboard");
    }
    onSubmit(values);
  };

  return (
    <Form
      form={form}
      initialValues={{ identity: { email: "" } }}
      onFinish={handleFinish}
      layout="vertical"
    >
      <Flex vertical className="mt-4">
        <Form.Item
          name={["identity", "email"]}
          label="User email address"
          rules={[
            { required: true, message: "Email Address is required" },
            { type: "email", message: "Email Address must be a valid email" },
          ]}
          layout="vertical"
        >
          <Input data-testid="input-identity.email" />
        </Form.Item>
        <div className="flex gap-4 self-end">
          <Button
            onClick={() => {
              form.resetFields();
              onCancel();
            }}
          >
            Cancel
          </Button>
          <Button
            htmlType="submit"
            type="primary"
            disabled={!isDirty || !isFormValid}
            data-testid="submit-btn"
            icon={<Icons.Link />}
          >
            Copy
          </Button>
        </div>
      </Flex>
    </Form>
  );
};

export default SubmitPrivacyRequestForm;
