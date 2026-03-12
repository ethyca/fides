import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import { Avatar, Flex, Icons, Text } from "fidesui";

import styles from "./ActionNode.module.scss";

export interface ActionNodeData extends Record<string, unknown> {}

export type ActionNodeType = Node<ActionNodeData, "actionNode">;

const ActionNode = ({ data }: NodeProps<ActionNodeType>) => (
  <div className={styles.node} data-testid="action-node">
    <Handle type="target" position={Position.Left} className={styles.handle} />
    <Flex align="center" gap="small" className={styles.header}>
      <Avatar
        shape="square"
        size="small"
        icon={<Icons.Fork size={16} />}
        className={styles.avatar}
      />
      <Text strong>Action</Text>
    </Flex>
    <div className={styles.placeholder}>
      <Text type="secondary">Placeholder</Text>
    </div>
    <Handle
      type="source"
      position={Position.Right}
      className={styles.handle}
    />
  </div>
);

export default ActionNode;
