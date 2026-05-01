import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import { Avatar, Flex, Icons, Tag, Text } from "fidesui";

import { ManualTaskNodeData } from "../types";
import styles from "./IntegrationNode.module.scss";

export type ManualTaskNodeType = Node<ManualTaskNodeData, "manualTask">;

const ManualTaskNode = ({ data }: NodeProps<ManualTaskNodeType>) => {
  const primaryField = data.fields[0];
  const primaryLabel = primaryField?.label ?? primaryField?.name;
  const primaryHelp = primaryField?.help_text;
  const extraCount = Math.max(0, data.fields.length - 1);

  return (
    <div className={styles.node} data-testid={`manual-task-node:${data.id}`}>
      <Flex align="center" gap="small" className={styles.header}>
        <Avatar
          shape="square"
          size="small"
          icon={<Icons.Activity size={16} />}
          className={styles.avatar}
        />
        <Text strong style={{ flex: 1 }} ellipsis={{ tooltip: data.name }}>
          {data.name}
        </Text>
      </Flex>
      <div className={styles.body}>
        {primaryLabel && (
          <Text
            style={{ fontSize: 12, display: "block" }}
            ellipsis={{ tooltip: primaryLabel }}
          >
            {primaryLabel}
          </Text>
        )}
        {primaryHelp && (
          <Text
            type="secondary"
            style={{ fontSize: 11, display: "block", marginTop: 2 }}
            ellipsis={{ tooltip: primaryHelp }}
          >
            {primaryHelp}
          </Text>
        )}
        {extraCount > 0 && (
          <Text
            type="secondary"
            style={{ fontSize: 11, display: "block", marginTop: 4 }}
          >
            +{extraCount} more field{extraCount === 1 ? "" : "s"}
          </Text>
        )}
        {data.conditions.length > 0 && (
          <Tag color="warning" style={{ fontSize: 10, marginTop: 6 }}>
            {data.conditions.length} condition
            {data.conditions.length === 1 ? "" : "s"}
          </Tag>
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

export default ManualTaskNode;
