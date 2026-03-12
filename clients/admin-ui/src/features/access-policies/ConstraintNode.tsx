import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import { Avatar, Flex, Icons, Text } from "fidesui";

import styles from "./ConstraintNode.module.scss";

export interface ConstraintNodeData extends Record<string, unknown> {}

export type ConstraintNodeType = Node<ConstraintNodeData, "constraintNode">;

const ConstraintNode = ({ data }: NodeProps<ConstraintNodeType>) => (
  <div className={styles.node} data-testid="constraint-node">
    <Handle type="target" position={Position.Left} className={styles.handle} />
    <Flex align="center" gap="small" className={styles.header}>
      <Avatar
        shape="square"
        size="small"
        icon={<Icons.Locked size={16} />}
        className={styles.avatar}
      />
      <Text strong>Constraint</Text>
    </Flex>
    <div className={styles.placeholder}>
      <Text type="secondary">Placeholder</Text>
    </div>
    <Handle type="source" position={Position.Right} className={styles.handle} />
  </div>
);

export default ConstraintNode;
