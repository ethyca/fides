import { Collapse, Drawer, Flex, Tag, Text } from "fidesui";

import {
  IntegrationNodeData,
  PreviewEdge,
  TraversalPreviewResponse,
} from "../types";

interface Props {
  data: IntegrationNodeData | null;
  edges: PreviewEdge[];
  integrations: TraversalPreviewResponse["integrations"];
  onClose: () => void;
}

const IntegrationDetailPanel = ({
  data,
  edges,
  integrations,
  onClose,
}: Props) => {
  if (!data) {
    return null;
  }

  const labelById = new Map<string, string>(
    integrations.map((i) => [i.id, i.connection_key]),
  );
  labelById.set("identity-root", "Identity");

  const incoming = edges
    .filter((e) => e.kind === "depends_on" && e.target === data.id)
    .map((e) => ({
      sourceLabel: labelById.get(e.source) ?? e.source,
      count: e.dep_count ?? 1,
    }))
    .sort((a, b) => b.count - a.count);

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
        {incoming.length > 0 && (
          <Flex vertical gap={4}>
            <Text strong>Depends on</Text>
            {incoming.map(({ sourceLabel, count }) => (
              <Text key={sourceLabel} style={{ fontSize: 13 }}>
                {sourceLabel}
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {" · "}
                  {count} field reference{count === 1 ? "" : "s"}
                </Text>
              </Text>
            ))}
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
