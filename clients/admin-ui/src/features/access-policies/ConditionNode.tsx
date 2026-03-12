import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import { Avatar, Flex, Icons, Text } from "fidesui";

import styles from "./ConditionNode.module.scss";
import NodeActions from "./NodeActions";

export interface ConditionNodeData extends Record<string, unknown> {
  onAddNode?: () => void;
  onAddCondition?: () => void;
  hasChildren?: boolean;
}

export type ConditionNodeType = Node<ConditionNodeData, "conditionNode">;

const ConditionNode = ({ data }: NodeProps<ConditionNodeType>) => (
  <div className={styles.node} data-testid="condition-node">
    <Handle type="target" position={Position.Left} className={styles.handle} />
    <Flex align="center" gap="small" className={styles.header}>
      <Avatar
        shape="square"
        size="small"
        icon={<Icons.SettingsAdjust size={16} />}
        className={styles.avatar}
      />
      <Text strong>Condition</Text>
    </Flex>
    <div className={styles.placeholder}>
      <Text type="secondary">Placeholder</Text>
    </div>
    {!data.hasChildren && (
      <NodeActions
        onAddNode={data.onAddNode}
        onAddCondition={data.onAddCondition}
        showAddAction={false}
      />
    )}
    <Handle type="source" position={Position.Right} className={styles.handle} />
  </div>
);

export default ConditionNode;
