import { Button, Card, Flex, Form, Input, Select, Space, Spin } from "fidesui";
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

interface Props {
  property?: Property;
  isLoading?: boolean;
  handleSubmit: (values: FormValues) => Promise<void>;
}

export interface FormValues {
  id?: string | null;
  name: string;
  type: PropertyType;
  messaging_templates?: Array<MinimalMessagingTemplate> | null;
  experiences: Array<MinimalPrivacyExperienceConfig>;
}

export const PropertyForm = ({ property, isLoading, handleSubmit }: Props) => {
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
      },
    [property],
  );

  // Re-initialize form when property data loads
  useEffect(() => {
    if (property) {
      form.setFieldsValue({
        ...property,
        messaging_templates: property.messaging_templates ?? undefined,
      });
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
                  <Space.Compact>
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
            >
              Save
            </Button>
          </Flex>
        </Flex>
      </Flex>
    </Form>
  );
};
