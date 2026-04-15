import {
  Button,
  Card,
  Checkbox,
  Collapse,
  Flex,
  Form,
  Input,
  Select,
  Tag,
  Text,
} from "fidesui";
import { useCallback, useState } from "react";

import { SYSTEM_TYPE_OPTIONS } from "../../constants";
import type { MockSystem } from "../../types";

const getIntegrationStatusColor = (
  status: string,
): "success" | "error" | "default" => {
  if (status === "active") {
    return "success";
  }
  if (status === "failed") {
    return "error";
  }
  return "default";
};

interface ConfigTabProps {
  system: MockSystem;
}

const ConfigTab = ({ system }: ConfigTabProps) => {
  const [form] = Form.useForm();
  const [isDirty, setIsDirty] = useState(false);

  const handleSave = useCallback(() => {
    setIsDirty(false);
  }, []);

  const handleReset = useCallback(() => {
    form.resetFields();
    setIsDirty(false);
  }, [form]);

  const purposeOptions = [
    "Analytics",
    "Finance",
    "Fraud prevention",
    "Marketing",
    "Customer support",
    "HR",
  ].map((p) => ({ label: p, value: p }));

  const roleOptions = [
    { label: "Producer", value: "producer" },
    { label: "Consumer", value: "consumer" },
  ];

  const responsibilityOptions = [
    { label: "Controller", value: "Controller" },
    { label: "Processor", value: "Processor" },
    { label: "Sub-Processor", value: "Sub-Processor" },
  ];

  const panels = [
    {
      key: "info",
      label: "System Information",
      children: (
        <Flex vertical gap={16}>
          <Form.Item label="Name" name="name">
            <Input />
          </Form.Item>
          <Form.Item label="System type" name="system_type">
            <Select aria-label="System type" options={SYSTEM_TYPE_OPTIONS} />
          </Form.Item>
          <Form.Item label="Department" name="department">
            <Input />
          </Form.Item>
          <Form.Item label="Responsibility" name="responsibility">
            <Select
              aria-label="Responsibility"
              options={responsibilityOptions}
            />
          </Form.Item>
          <Form.Item label="Group" name="group">
            <Input />
          </Form.Item>
          <Form.Item label="Description" name="description">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item label="Roles" name="roles">
            <Checkbox.Group options={roleOptions} />
          </Form.Item>
          <Form.Item label="Stewards" name="stewards">
            <Select
              aria-label="Stewards"
              mode="multiple"
              placeholder="Select stewards"
              options={system.stewards.map((st) => ({
                label: st.name,
                value: st.initials,
              }))}
            />
          </Form.Item>
        </Flex>
      ),
    },
    {
      key: "purposes",
      label: "Uses & purposes",
      children: (
        <Flex vertical gap={12}>
          <Text type="secondary">
            Assign purposes to describe how this system processes personal data.
          </Text>
          <Form.Item name="purposes">
            <Select
              aria-label="Purposes"
              mode="multiple"
              placeholder="Select purposes"
              options={purposeOptions}
            />
          </Form.Item>
          <Text type="secondary" className="text-xs">
            Current:
          </Text>
          <Flex gap={4} wrap>
            {system.purposes.length > 0 ? (
              system.purposes.map((p) => (
                <Tag key={p.name} bordered={false}>
                  {p.name}
                </Tag>
              ))
            ) : (
              <Text type="secondary">No purposes defined</Text>
            )}
          </Flex>
        </Flex>
      ),
    },
    {
      key: "dataflow",
      label: "Data Flow",
      children: (
        <Flex vertical gap={12}>
          <Text type="secondary">
            Configure data flow relationships with other systems.
          </Text>
          {system.relationships.length > 0 ? (
            system.relationships.map((rel) => (
              <Card key={rel.systemKey} size="small">
                <Flex justify="space-between" align="center">
                  <Flex vertical>
                    <Text strong>{rel.systemName}</Text>
                    <Text type="secondary" className="text-xs">
                      {rel.role === "producer"
                        ? "Producing for"
                        : "Consuming from"}{" "}
                      &middot; {rel.declaredUse}
                    </Text>
                  </Flex>
                  {rel.hasViolation && (
                    <Tag color="error" bordered={false}>
                      Violation
                    </Tag>
                  )}
                </Flex>
              </Card>
            ))
          ) : (
            <Text type="secondary">No data flow relationships configured.</Text>
          )}
        </Flex>
      ),
    },
    {
      key: "integrations",
      label: "Integrations",
      children: (
        <Flex vertical gap={12}>
          <Text type="secondary">
            Manage integrations and connections for this system.
          </Text>
          {system.integrations.length > 0 ? (
            system.integrations.map((intg) => (
              <Card key={intg.name} size="small">
                <Flex justify="space-between" align="center">
                  <Flex vertical>
                    <Text strong>{intg.name}</Text>
                    <Text type="secondary" className="text-xs">
                      {intg.type} &middot; {intg.accessLevel} &middot;{" "}
                      {intg.enabledActions.join(", ")}
                    </Text>
                  </Flex>
                  <Tag
                    color={getIntegrationStatusColor(intg.status)}
                    bordered={false}
                  >
                    {intg.status}
                  </Tag>
                </Flex>
              </Card>
            ))
          ) : (
            <Text type="secondary">No integrations configured.</Text>
          )}
        </Flex>
      ),
    },
  ];

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={{
        name: system.name,
        system_type: system.system_type,
        department: system.department,
        responsibility: system.responsibility,
        group: system.group ?? "",
        description: system.description,
        roles: system.roles,
        stewards: system.stewards.map((st) => st.initials),
        purposes: system.purposes.map((p) => p.name),
      }}
      onValuesChange={() => setIsDirty(true)}
    >
      <Flex vertical gap={16}>
        <Collapse defaultActiveKey={["info"]} items={panels} accordion />
        <Flex gap={8} justify="flex-end">
          <Button onClick={handleReset} disabled={!isDirty}>
            Cancel
          </Button>
          <Button type="primary" onClick={handleSave} disabled={!isDirty}>
            Save changes
          </Button>
        </Flex>
      </Flex>
    </Form>
  );
};

export default ConfigTab;
