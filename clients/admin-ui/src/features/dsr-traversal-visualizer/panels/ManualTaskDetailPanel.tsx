import { Drawer, Flex, Tag, Text } from "fidesui";

import { IntegrationNodeData, ManualTaskNodeData } from "../types";

interface Props {
  data: ManualTaskNodeData | null;
  integrations: IntegrationNodeData[];
  onClose: () => void;
}

export const ManualTaskDetailPanel = ({
  data,
  integrations,
  onClose,
}: Props) => {
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
              <Flex key={c.expression} vertical className="mb-2">
                <Text>{c.summary}</Text>
                <Text type="secondary" className="font-mono text-xs">
                  {c.expression}
                </Text>
              </Flex>
            ))}
          </Flex>
        )}
        {data.fields.length > 0 && (
          <Flex vertical gap="small">
            <Text strong>Required Fields</Text>
            {data.fields.map((f) => (
              <Flex key={f.name} vertical gap={2}>
                <Flex gap={6} align="baseline">
                  <Text>{f.label ?? f.name}</Text>
                  <Tag>{f.type}</Tag>
                  {f.required && <Tag color="error">required</Tag>}
                </Flex>
                {f.help_text && (
                  <Text type="secondary" className="text-xs">
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
                <Text key={id} data-testid="gated-integration">
                  {name}
                </Text>
              );
            })}
          </Flex>
        )}
      </Flex>
    </Drawer>
  );
};
