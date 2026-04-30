import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import { Avatar, Flex, Icons, Tag, Text } from "fidesui";

import { ManualTaskNodeData } from "../types";
import styles from "./IntegrationNode.module.scss";

export type ManualTaskNodeType = Node<ManualTaskNodeData, "manualTask">;

const ManualTaskNode = ({ data }: NodeProps<ManualTaskNodeType>) => (
  <div className={styles.node} data-testid={`manual-task-node:${data.id}`}>
    <Flex align="center" gap="small" className={styles.header}>
      <Avatar
        shape="square"
        size="small"
        icon={<Icons.Activity size={16} />}
        className={styles.avatar}
      />
      <Text strong style={{ flex: 1 }}>
        {data.name}
      </Text>
    </Flex>
    <div className={styles.body}>
      {data.conditions.length > 0 && (
        <Tag color="warning" style={{ fontSize: 10 }}>
          {data.conditions.length} condition
          {data.conditions.length === 1 ? "" : "s"}
        </Tag>
      )}
      {data.assignees.length > 0 && (
        <Text
          type="secondary"
          style={{ fontSize: 12, display: "block", marginTop: 6 }}
        >
          Assigned: {data.assignees.map((a) => a.name).join(", ")}
        </Text>
      )}
    </div>
    <Handle
      type="source"
      position={Position.Right}
      className={styles.handle}
    />
  </div>
);

export default ManualTaskNode;
