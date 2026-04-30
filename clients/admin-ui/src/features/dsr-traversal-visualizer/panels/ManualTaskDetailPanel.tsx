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
          <Flex vertical>
            <Text strong>Fields</Text>
            <Flex gap={4} wrap>
              {data.fields.map((f) => (
                <Tag key={f.name}>
                  {f.name}: {f.type}
                </Tag>
              ))}
            </Flex>
          </Flex>
        )}
      </Flex>
    </Drawer>
  );
};

export default ManualTaskDetailPanel;
