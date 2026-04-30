import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import { Avatar, Flex, Tag, Text } from "fidesui";

import { REACHABILITY_COLOR, REACHABILITY_LABEL } from "../constants";
import { IntegrationNodeData } from "../types";
import styles from "./IntegrationNode.module.scss";

export type IntegrationNodeType = Node<IntegrationNodeData, "integration">;

const IntegrationNode = ({ data }: NodeProps<IntegrationNodeType>) => {
  const {
    connection_key: connectionKey,
    connector_type: connectorType,
    system,
    reachability,
    collection_count: collectionCount,
    data_categories: dataCategories,
  } = data;
  return (
    <div
      className={styles.node}
      data-testid={`integration-node:${connectionKey}`}
    >
      <Handle
        type="target"
        position={Position.Left}
        className={styles.handle}
      />
      <Flex align="center" gap="small" className={styles.header}>
        <Avatar shape="square" size="small" className={styles.avatar}>
          {connectorType[0]?.toUpperCase()}
        </Avatar>
        <Flex vertical style={{ flex: 1, minWidth: 0 }}>
          <Text strong ellipsis={{ tooltip: connectionKey }}>
            {connectionKey}
          </Text>
          {system?.name && (
            <Text
              type="secondary"
              style={{ fontSize: 12 }}
              ellipsis={{ tooltip: system.name }}
            >
              {system.name}
            </Text>
          )}
        </Flex>
      </Flex>
      <div className={styles.body}>
        <Flex justify="space-between" align="center" gap="small">
          <Text type="secondary" style={{ fontSize: 12 }}>
            {collectionCount.traversed} of {collectionCount.total} collections
          </Text>
          <Tag color={REACHABILITY_COLOR[reachability]} style={{ margin: 0 }}>
            {REACHABILITY_LABEL[reachability]}
          </Tag>
        </Flex>
        {dataCategories.length > 0 && (
          <Flex gap={4} wrap style={{ marginTop: 6 }}>
            {dataCategories.slice(0, 3).map((dc) => (
              <Tag key={dc} style={{ fontSize: 10, margin: 0 }}>
                {dc}
              </Tag>
            ))}
            {dataCategories.length > 3 && (
              <Tag style={{ fontSize: 10, margin: 0 }}>
                +{dataCategories.length - 3}
              </Tag>
            )}
          </Flex>
        )}
      </div>
      <Handle
        type="source"
        position={Position.Right}
        className={styles.handle}
      />
    </div>
  );
};

export default IntegrationNode;
