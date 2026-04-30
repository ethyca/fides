import { Collapse, Drawer, Flex, Tag, Text } from "fidesui";

import { IntegrationNodeData } from "../types";

interface Props {
  data: IntegrationNodeData | null;
  onClose: () => void;
}

const IntegrationDetailPanel = ({ data, onClose }: Props) => {
  if (!data) {
    return null;
  }
  return (
    <Drawer
      open
      onClose={onClose}
      title={data.connection_key}
      placement="right"
      width={420}
    >
      <Flex vertical gap="middle">
        <Text type="secondary" style={{ fontSize: 12 }}>
          {data.connector_type} · {data.collection_count.traversed} of{" "}
          {data.collection_count.total} collections
        </Text>
        {data.system && (
          <Flex vertical>
            <Text strong>System</Text>
            <Text>
              {data.system.name}
              {data.system.data_use ? ` · ${data.system.data_use}` : ""}
            </Text>
          </Flex>
        )}
        <Flex vertical>
          <Text strong>Datasets</Text>
          <Collapse
            ghost
            size="small"
            items={data.datasets.map((ds) => ({
              key: ds.fides_key,
              label: ds.fides_key,
              children: (
                <Flex vertical gap={6}>
                  {ds.collections.map((c) => (
                    <Flex key={c.name} vertical>
                      <Text>
                        {c.name}
                        {c.skipped ? " (skipped)" : ""}
                      </Text>
                      <Flex gap={4} wrap>
                        {c.fields.flatMap((f) =>
                          f.data_categories.map((dc) => (
                            <Tag
                              key={`${c.name}.${f.name}.${dc}`}
                              style={{ fontSize: 10 }}
                            >
                              {dc}
                            </Tag>
                          )),
                        )}
                      </Flex>
                    </Flex>
                  ))}
                </Flex>
              ),
            }))}
          />
        </Flex>
      </Flex>
    </Drawer>
  );
};

export default IntegrationDetailPanel;
