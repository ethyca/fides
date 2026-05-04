import { Drawer, Flex, Tag, Text } from "fidesui";

import { IntegrationNodeData, ManualTaskNodeData } from "../types";

interface Props {
  data: ManualTaskNodeData | null;
  integrations: IntegrationNodeData[];
  onClose: () => void;
}

const ManualTaskDetailPanel = ({ data, integrations, onClose }: Props) => {
  if (!data) {
    return null;
  }
  return (
    <Drawer
      open
      onClose={onClose}
      title={data.name}
      placement="right"
      width={420}
    >
      <Flex vertical gap="middle">
        {data.assignees.length > 0 && (
          <Flex vertical>
            <Text strong>Assignees</Text>
            {data.assignees.map((a) => (
              <Text key={a.name}>
                {a.name} ({a.type})
              </Text>
            ))}
          </Flex>
        )}
        {data.conditions.length > 0 && (
          <Flex vertical>
            <Text strong>Conditions</Text>
            {data.conditions.map((c) => (
              <Flex key={c.expression} vertical style={{ marginBottom: 8 }}>
                <Text>{c.summary}</Text>
                <Text
                  type="secondary"
                  style={{ fontSize: 11, fontFamily: "monospace" }}
                >
                  {c.expression}
                </Text>
              </Flex>
            ))}
          </Flex>
        )}
        {data.fields.length > 0 && (
          <Flex vertical gap={8}>
            <Text strong>Required Fields</Text>
            {data.fields.map((f) => (
              <Flex key={f.name} vertical gap={2}>
                <Flex gap={6} align="baseline">
                  <Text>{f.label ?? f.name}</Text>
                  <Tag style={{ fontSize: 10, margin: 0 }}>{f.type}</Tag>
                  {f.required && (
                    <Tag color="error" style={{ fontSize: 10, margin: 0 }}>
                      required
                    </Tag>
                  )}
                </Flex>
                {f.help_text && (
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {f.help_text}
                  </Text>
                )}
              </Flex>
            ))}
          </Flex>
        )}
        {data.gates && data.gates.length > 0 && (
          <Flex vertical>
            <Text strong>Gates</Text>
            {data.gates.map((id) => {
              const integration = integrations.find((i) => i.id === id);
              const name =
                integration?.system?.name ?? integration?.connection_key ?? id;
              return (
                <div key={id} data-testid="gated-integration">
                  {name}
                </div>
              );
            })}
          </Flex>
        )}
      </Flex>
    </Drawer>
  );
};

export default ManualTaskDetailPanel;
