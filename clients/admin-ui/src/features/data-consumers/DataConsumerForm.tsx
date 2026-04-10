import { Button, Flex, Form, Input, Select, Spin } from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useState } from "react";

import { DATA_CONSUMERS_ROUTE } from "~/features/common/nav/routes";
import { useGetAllDataPurposesQuery } from "~/features/data-purposes/data-purpose.slice";

import {
  DataConsumer,
  useGetAvailableScopesQuery,
} from "./data-consumer.slice";
import useConsumerTypeOptions from "./useConsumerTypeOptions";

const getDisplayNameForScope = (
  scope: Record<string, string>,
  type: string,
): string => {
  if (type === "google_group") {
    return scope.group_email ?? "";
  }
  if (type === "gcp_iam_role") {
    return scope.role ?? "";
  }
  if (type === "gcp_service_account") {
    return scope.email ?? "";
  }
  return Object.values(scope).join(", ");
};

export interface DataConsumerFormValues {
  name: string;
  type: string;
  scope: Record<string, string>;
  description: string;
  purposeFidesKeys: string[];
}

interface DataConsumerFormProps {
  consumer?: DataConsumer;
  handleSubmit: (values: DataConsumerFormValues) => Promise<void>;
}

const DataConsumerForm = ({
  consumer,
  handleSubmit,
}: DataConsumerFormProps) => {
  const [form] = Form.useForm<DataConsumerFormValues>();
  const router = useRouter();

  const { data: purposesData, isLoading: purposesLoading } =
    useGetAllDataPurposesQuery({ size: 200 });

  const {
    typeOptions,
    getConsumerType,
    isLoading: typesLoading,
  } = useConsumerTypeOptions();

  const { data: availableScopes, isLoading: scopesLoading } =
    useGetAvailableScopesQuery();

  const selectedType = Form.useWatch("type", form);
  const [selectedScopeValue, setSelectedScopeValue] = useState<
    string | undefined
  >(
    consumer?.scope && Object.keys(consumer.scope).length > 0
      ? JSON.stringify(consumer.scope)
      : undefined,
  );

  // Clear scope when type changes (only after user interaction)
  useEffect(() => {
    if (form.isFieldTouched("type")) {
      form.setFieldValue("scope", {});
      setSelectedScopeValue(undefined);
    }
  }, [selectedType, form]);

  // Filter available scopes to selected type
  const scopeOptionsForType = useMemo(() => {
    if (!selectedType || !availableScopes) {
      return [];
    }
    return availableScopes
      .filter((s) => s.type === selectedType)
      .map((s) => ({
        value: JSON.stringify(s.scope),
        label: s.display_name,
        scope: s.scope,
      }));
  }, [selectedType, availableScopes]);

  // On edit, include the current consumer's scope as an option
  const allScopeOptions = useMemo(() => {
    if (!consumer?.scope || !Object.keys(consumer.scope).length) {
      return scopeOptionsForType;
    }
    const currentScopeJson = JSON.stringify(consumer.scope);
    const alreadyIncluded = scopeOptionsForType.some(
      (o) => o.value === currentScopeJson,
    );
    if (alreadyIncluded) {
      return scopeOptionsForType;
    }
    // Add current scope as an option (it's already assigned to this consumer)
    const currentType = getConsumerType(consumer.type);
    const displayName = getDisplayNameForScope(consumer.scope, consumer.type);
    return [
      {
        value: currentScopeJson,
        label: `${displayName}${currentType ? "" : ` (${consumer.type})`}`,
        scope: consumer.scope,
      },
      ...scopeOptionsForType,
    ];
  }, [scopeOptionsForType, consumer, getConsumerType]);

  const handleScopeSelect = useCallback(
    (value: string) => {
      const scope = JSON.parse(value) as Record<string, string>;
      form.setFieldsValue({ scope });
      setSelectedScopeValue(value);
    },
    [form],
  );

  const purposeOptions = useMemo(
    () =>
      (purposesData?.items ?? []).map((p) => ({
        value: p.fides_key,
        label: p.name || p.fides_key,
      })),
    [purposesData],
  );

  const initialValues = useMemo<DataConsumerFormValues>(
    () => ({
      name: consumer?.name ?? "",
      type: consumer?.type ?? "",
      scope: consumer?.scope ?? {},
      description: consumer?.description ?? "",
      purposeFidesKeys: consumer?.purpose_fides_keys ?? [],
    }),
    [consumer],
  );

  const handleCancel = useCallback(() => {
    router.push(DATA_CONSUMERS_ROUTE);
  }, [router]);

  if (purposesLoading || typesLoading || scopesLoading) {
    return (
      <Flex justify="center" align="center" className="py-12">
        <Spin />
      </Flex>
    );
  }

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
      initialValues={initialValues}
      key={consumer?.id ?? "create"}
      data-testid="data-consumer-form"
      style={{ maxWidth: 720 }}
    >
      <Form.Item
        name="type"
        label="Type"
        rules={[{ required: true, message: "Type is required" }]}
        tooltip="The identity type used to resolve this consumer in query logs"
      >
        <Select
          placeholder="Select consumer type"
          options={typeOptions}
          showSearch
          filterOption={(input, option) =>
            String(option?.label ?? "")
              .toLowerCase()
              .includes(input.toLowerCase())
          }
          aria-label="Type"
          data-testid="data-consumer-type-select"
        />
      </Form.Item>

      {/* Hidden form item to track scope in form values */}
      <Form.Item
        name="scope"
        hidden
        rules={[
          {
            validator: (_, value) =>
              value && Object.keys(value).length > 0
                ? Promise.resolve()
                : Promise.reject(new Error("Scope is required")),
          },
        ]}
      >
        <Input />
      </Form.Item>

      {selectedType && allScopeOptions.length > 0 && (
        <Form.Item
          label="Scope"
          rules={[{ required: true, message: "Scope is required" }]}
          tooltip="The specific identity to associate with this consumer"
        >
          <Select
            placeholder="Select scope"
            options={allScopeOptions}
            value={selectedScopeValue}
            onChange={handleScopeSelect}
            showSearch
            filterOption={(input, option) =>
              String(option?.label ?? "")
                .toLowerCase()
                .includes(input.toLowerCase())
            }
            aria-label="Scope"
            data-testid="data-consumer-scope-select"
          />
        </Form.Item>
      )}

      <Form.Item
        name="name"
        label="Name"
        rules={[{ required: true, message: "Name is required" }]}
      >
        <Input
          placeholder="Enter consumer name"
          data-testid="data-consumer-name-input"
        />
      </Form.Item>

      <Form.Item
        name="purposeFidesKeys"
        label="Assigned purposes"
        tooltip="Which data purposes is this consumer authorized for?"
      >
        <Select
          mode="multiple"
          placeholder="Select purposes"
          options={purposeOptions}
          aria-label="Assigned purposes"
          data-testid="data-consumer-purposes-select"
        />
      </Form.Item>

      <Form.Item
        name="description"
        label="Description"
        tooltip="An optional description of this data consumer"
      >
        <Input.TextArea
          placeholder="Enter a description"
          rows={3}
          data-testid="data-consumer-description-input"
        />
      </Form.Item>

      <Flex justify="space-between" className="pt-4">
        <Button onClick={handleCancel} data-testid="cancel-button">
          Cancel
        </Button>
        <Button
          type="primary"
          htmlType="submit"
          data-testid="save-data-consumer-button"
        >
          Save
        </Button>
      </Flex>
    </Form>
  );
};

export default DataConsumerForm;
