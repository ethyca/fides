import {
  Button,
  Card,
  Flex,
  Form,
  Icons,
  Input,
  Select,
  Space,
  Spin,
} from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useState } from "react";

import ClipboardButton from "~/features/common/ClipboardButton";
import { enumToOptions } from "~/features/common/helpers";
import { InfoTooltip } from "~/features/common/InfoTooltip";
import { PROPERTIES_ROUTE } from "~/features/common/nav/routes";
import { useGetAllExperienceConfigsQuery } from "~/features/privacy-experience/privacy-experience.slice";
import {
  MinimalMessagingTemplate,
  MinimalPrivacyExperienceConfig,
  Property,
  PropertyType,
} from "~/types/api";

import DeletePropertyModal from "./DeletePropertyModal";
import {
  PrivacyCenterConfigSection,
  PrivacyCenterConfigValue,
} from "./privacy-center-config/PrivacyCenterConfigSection";

const PCConfigSectionAdapter = ({
  propertyId,
  value,
  onChange,
  onDeleteImmediately,
  onSaveImmediately,
}: {
  propertyId: string;
  value?: PrivacyCenterConfigValue | null;
  onChange?: (next: PrivacyCenterConfigValue) => void;
  onDeleteImmediately?: (nextConfig: PrivacyCenterConfigValue) => Promise<void>;
  onSaveImmediately?: (nextConfig: PrivacyCenterConfigValue) => Promise<void>;
}) => (
  <PrivacyCenterConfigSection
    propertyId={propertyId}
    value={value ?? null}
    onChange={(next) => onChange?.(next)}
    onDeleteImmediately={onDeleteImmediately}
    onSaveImmediately={onSaveImmediately}
  />
);

interface Props {
  property?: Property;
  isLoading?: boolean;
  handleSubmit: (values: FormValues) => Promise<void>;
  onDeleteAction?: (nextConfig: PrivacyCenterConfigValue) => Promise<void>;
  onSaveAction?: (nextConfig: PrivacyCenterConfigValue) => Promise<void>;
}

export interface FormValues {
  id?: string | null;
  name: string;
  type: PropertyType;
  paths: Array<string>;
  messaging_templates?: Array<MinimalMessagingTemplate> | null;
  experiences: Array<MinimalPrivacyExperienceConfig>;
  privacy_center_config?: PrivacyCenterConfigValue | null;
}

export const PropertyForm = ({
  property,
  isLoading,
  handleSubmit,
  onDeleteAction,
  onSaveAction,
}: Props) => {
  const router = useRouter();
  const [form] = Form.useForm<FormValues>();
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load experience configs for the multi-select
  const { data: experienceData, isLoading: experiencesLoading } =
    useGetAllExperienceConfigsQuery({
      page: 1,
      size: 100,
    });
  const experienceConfigs = useMemo(
    () => experienceData?.items ?? [],
    [experienceData],
  );

  const experienceOptions = useMemo(
    () => experienceConfigs.map((exp) => ({ value: exp.id, label: exp.name })),
    [experienceConfigs],
  );

  // Transform selected IDs back to MinimalPrivacyExperienceConfig objects
  const handleExperienceChange = useCallback(
    (selectedIds: string[]) =>
      selectedIds
        .map((id) => {
          const config = experienceConfigs.find((e) => e.id === id);
          return config ? { id: config.id, name: config.name } : undefined;
        })
        .filter(Boolean) as MinimalPrivacyExperienceConfig[],
    [experienceConfigs],
  );

  // Track valid state for submit button
  const allValues = Form.useWatch([], form);
  const [submittable, setSubmittable] = useState(false);

  useEffect(() => {
    form
      .validateFields({ validateOnly: true })
      .then(() => setSubmittable(true))
      .catch(() => setSubmittable(false));
  }, [form, allValues]);

  const initialValues = useMemo(
    () =>
      property || {
        name: "",
        type: PropertyType.WEBSITE,
        experiences: [],
        messaging_templates: [],
        paths: [],
        privacy_center_config: null,
      },
    [property],
  );

  // Re-initialize form when property data loads
  useEffect(() => {
    if (property) {
      form.setFieldsValue({
        ...property,
        messaging_templates: property.messaging_templates ?? undefined,
      } as Parameters<typeof form.setFieldsValue>[0]);
    }
  }, [property, form]);

  const handleCancel = () => {
    router.push(PROPERTIES_ROUTE);
  };

  const onFinish = async (values: FormValues) => {
    setIsSubmitting(true);
    try {
      await handleSubmit(values);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={initialValues}
      onFinish={onFinish}
    >
      <Flex vertical gap="large">
        <Card title="Property details">
          {isLoading ? (
            <Flex justify="center" align="center" className="min-h-72">
              <Spin />
            </Flex>
          ) : (
            <>
              <Form.Item
                name="name"
                label={
                  <Flex align="center" gap={4}>
                    Property name
                    <InfoTooltip label="Unique name to identify this property" />
                  </Flex>
                }
                rules={[
                  { required: true, message: "Property name is required" },
                ]}
              >
                <Input data-testid="input-name" />
              </Form.Item>
              <Form.Item
                name="type"
                label="Type"
                rules={[{ required: true, message: "Type is required" }]}
              >
                <Select
                  aria-label="Type"
                  options={enumToOptions(PropertyType)}
                  data-testid="input-type"
                />
              </Form.Item>
              <Form.Item
                label="Privacy center paths"
                tooltip="Paths under your privacy center this property responds to. Each path must be unique across properties."
              >
                <Form.List name="paths">
                  {(fields, { add, remove }) => (
                    <Flex vertical>
                      {fields.map((field) => (
                        <Flex className="my-1" key={field.key}>
                          <Form.Item name={field.name} className="mb-0 grow">
                            <Input placeholder="/privacy" />
                          </Form.Item>
                          <Button
                            aria-label="Remove path"
                            className="ml-2"
                            icon={<Icons.TrashCan />}
                            onClick={() => remove(field.name)}
                          />
                        </Flex>
                      ))}
                      <Button className="mt-2" onClick={() => add("")}>
                        Add path
                      </Button>
                    </Flex>
                  )}
                </Form.List>
              </Form.Item>
              <Form.Item
                name="privacy_center_config"
                label="Privacy center config"
                valuePropName="value"
              >
                <PCConfigSectionAdapter
                  propertyId={property?.id ?? ""}
                  onDeleteImmediately={onDeleteAction}
                  onSaveImmediately={onSaveAction}
                />
              </Form.Item>
              <Form.Item
                name="experiences"
                label="Experiences"
                getValueProps={(value: MinimalPrivacyExperienceConfig[]) => ({
                  value: (value || []).map((exp) => exp.id),
                })}
                getValueFromEvent={handleExperienceChange}
              >
                <Select
                  aria-label="Experiences"
                  mode="multiple"
                  options={experienceOptions}
                  loading={experiencesLoading}
                  placeholder="Select experiences"
                  data-testid="input-experiences"
                  filterOption={(input, option) =>
                    (option?.label ?? "")
                      .toLowerCase()
                      .includes(input.toLowerCase())
                  }
                />
              </Form.Item>
              {property && (
                <Form.Item
                  label="Property ID"
                  tooltip="Automatically generated unique ID for this property, used for developer configurations"
                  className="!mb-0"
                >
                  <Space.Compact className="w-full">
                    <Input readOnly value={property.id ?? ""} />
                    <Space.Addon>
                      <ClipboardButton copyText={property.id ?? ""} />
                    </Space.Addon>
                  </Space.Compact>
                </Form.Item>
              )}
            </>
          )}
        </Card>
        <Flex justify="space-between">
          {property && (
            <DeletePropertyModal
              property={property}
              triggerComponent={
                <Button data-testid="delete-property-button">Delete</Button>
              }
            />
          )}
          <Flex justify="end" className="w-full pt-2">
            <Button onClick={handleCancel} className="mr-3">
              Cancel
            </Button>
            <Button
              htmlType="submit"
              type="primary"
              disabled={isSubmitting || !form.isFieldsTouched() || !submittable}
              loading={isSubmitting}
              data-testid="save-btn"
            >
              Save
            </Button>
          </Flex>
        </Flex>
      </Flex>
    </Form>
  );
};
