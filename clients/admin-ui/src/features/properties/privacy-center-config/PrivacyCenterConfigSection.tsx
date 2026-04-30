import { Button, Card, Flex, Form, Icons, Input, Select } from "fidesui";
import { useEffect, useMemo } from "react";

import { useGetPoliciesQuery } from "~/features/policies/policy.slice";
import type {
  fides__api__schemas__privacy_center_config__PrivacyCenterConfig as PrivacyCenterConfig,
  PrivacyRequestOption,
} from "~/types/api";

import { DEFAULT_PRIVACY_CENTER_CONFIG } from "../privacy-center/helpers";

export type PrivacyCenterConfigValue = PrivacyCenterConfig;

const DEFAULT_ACTION: PrivacyRequestOption = {
  icon_path: "",
  title: "",
  description: "",
  confirmButtonText: "Continue",
  cancelButtonText: "Cancel",
};

interface Props {
  propertyId: string;
  value: PrivacyCenterConfigValue | null;
  onChange?: (next: PrivacyCenterConfigValue) => void;
}

const ActionCard = ({ name }: { name: number }) => {
  const { data: policiesPage } = useGetPoliciesQuery();
  const policyOptions = useMemo(
    () =>
      (policiesPage?.items ?? []).map((p) => ({
        value: p.key ?? "",
        label: p.name,
      })),
    [policiesPage],
  );

  return (
    <>
      <Form.Item name={[name, "policy_key"]} label="Policy key">
        <Select
          aria-label="Policy key"
          options={policyOptions}
          allowClear
          placeholder="Select policy"
          data-testid={`action-policy-key-${name}`}
        />
      </Form.Item>
      <Form.Item name={[name, "icon_path"]} label="Icon path">
        <Input
          placeholder="https://example.com/icon.svg"
          data-testid={`action-icon-path-${name}`}
        />
      </Form.Item>
      <Form.Item
        name={[name, "title"]}
        label="Title"
        rules={[{ required: true, message: "Title is required" }]}
      >
        <Input data-testid={`action-title-${name}`} />
      </Form.Item>
      <Form.Item
        name={[name, "description"]}
        label="Description"
        rules={[{ required: true, message: "Description is required" }]}
      >
        <Input data-testid={`action-description-${name}`} />
      </Form.Item>
      <Form.Item name={[name, "confirmButtonText"]} label="Confirm button text">
        <Input data-testid={`action-confirm-text-${name}`} />
      </Form.Item>
      <Form.Item name={[name, "cancelButtonText"]} label="Cancel button text">
        <Input data-testid={`action-cancel-text-${name}`} />
      </Form.Item>
    </>
  );
};

export const PrivacyCenterConfigSection = ({
  propertyId: _propertyId,
  value,
  onChange,
}: Props) => {
  const [form] = Form.useForm<PrivacyCenterConfigValue>();

  useEffect(() => {
    if (value) {
      form.setFieldsValue(
        value as Parameters<typeof form.setFieldsValue>[0],
      );
    }
  }, [value, form]);

  const initialValues = useMemo(
    () => value ?? DEFAULT_PRIVACY_CENTER_CONFIG,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  const handleValuesChange = () => {
    onChange?.(form.getFieldsValue(true) as PrivacyCenterConfigValue);
  };

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={initialValues as Parameters<typeof form.setFieldsValue>[0]}
      onValuesChange={handleValuesChange}
    >
      <Flex vertical gap={16}>
        <Card title="General" size="small">
          <Form.Item
            name="title"
            label="Title"
            rules={[{ required: true, message: "Title is required" }]}
          >
            <Input data-testid="pc-config-title" />
          </Form.Item>
          <Form.Item
            name="description"
            label="Description"
            rules={[{ required: true, message: "Description is required" }]}
          >
            <Input data-testid="pc-config-description" />
          </Form.Item>
          <Form.Item name="logo_path" label="Logo path">
            <Input data-testid="pc-config-logo-path" />
          </Form.Item>
          <Form.Item name="logo_url" label="Logo URL">
            <Input data-testid="pc-config-logo-url" />
          </Form.Item>
          <Form.Item name="favicon_path" label="Favicon path">
            <Input data-testid="pc-config-favicon-path" />
          </Form.Item>
          <Form.Item name="privacy_policy_url" label="Privacy policy URL">
            <Input data-testid="pc-config-privacy-policy-url" />
          </Form.Item>
          <Form.Item
            name="privacy_policy_url_text"
            label="Privacy policy URL text"
            className="!mb-0"
          >
            <Input data-testid="pc-config-privacy-policy-url-text" />
          </Form.Item>
        </Card>

        <Card title="Actions" size="small">
          <Form.List name="actions">
            {(fields, { add, remove }) => (
              <Flex vertical gap={12}>
                {fields.map(({ key, name }) => (
                  <Card
                    key={key}
                    size="small"
                    extra={
                      <Button
                        aria-label="Remove action"
                        icon={<Icons.TrashCan />}
                        onClick={() => remove(name)}
                        disabled={fields.length === 1}
                        data-testid={`remove-action-${name}`}
                      />
                    }
                    title={`Action ${name + 1}`}
                  >
                    <ActionCard name={name} />
                  </Card>
                ))}
                <div>
                  <Button
                    icon={<Icons.Add />}
                    onClick={() => add({ ...DEFAULT_ACTION })}
                    data-testid="add-action-button"
                  >
                    Add action
                  </Button>
                </div>
              </Flex>
            )}
          </Form.List>
        </Card>
      </Flex>
    </Form>
  );
};
