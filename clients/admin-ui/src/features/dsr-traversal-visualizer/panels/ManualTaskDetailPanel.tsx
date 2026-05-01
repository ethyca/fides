import { Drawer, Flex, Tag, Text } from "fidesui";

import { ManualTaskNodeData } from "../types";

interface Props {
  data: ManualTaskNodeData | null;
  onClose: () => void;
}

const ManualTaskDetailPanel = ({ data, onClose }: Props) => {
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
            {data.conditions.map((c, idx) => (
              <Flex key={idx} vertical style={{ marginBottom: 8 }}>
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
            <Text strong>Fields</Text>
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
      </Flex>
    </Drawer>
  );
};

export default ManualTaskDetailPanel;
