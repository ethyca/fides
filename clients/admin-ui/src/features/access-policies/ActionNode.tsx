import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import { Avatar, Flex, Form, Icons, Radio, Text } from "fidesui";

import styles from "./ActionNode.module.scss";
import { ACTION_TYPE_OPTIONS } from "./constants";
import NodeActions from "./NodeActions";
import { ActionType } from "./types";

export interface ActionNodeData extends Record<string, unknown> {
  actionType?: ActionType;
  onActionTypeChange?: (value: ActionType) => void;
  onAddNode?: () => void;
  onAddCondition?: () => void;
  hasChildren?: boolean;
}

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
    <div className={styles.body}>
      <Form layout="vertical" className="nodrag">
        <Form.Item className="mb-0">
          <Radio.Group
            value={data.actionType}
            onChange={(e) => data.onActionTypeChange?.(e.target.value)}
            optionType="button"
            buttonStyle="solid"
            options={ACTION_TYPE_OPTIONS}
            className="w-full"
          />
        </Form.Item>
      </Form>
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

export default ActionNode;
