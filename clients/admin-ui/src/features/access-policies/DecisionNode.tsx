import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import { Avatar, Flex, Form, Icons, Input, Radio, Text } from "fidesui";

import { ACTION_TYPE_OPTIONS } from "./constants";
import styles from "./DecisionNode.module.scss";
import NodeActions from "./NodeActions";
import { ActionType } from "./types";

export interface ActionNodeData extends Record<string, unknown> {
  actionType?: ActionType;
  actionMessage?: string;
  onActionTypeChange?: (value: ActionType) => void;
  onActionMessageChange?: (value: string) => void;
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
      <Text strong>Decision</Text>
    </Flex>
    <div className={styles.body}>
      <Form layout="vertical" className="nodrag">
        <Form.Item
          className={data.actionType === ActionType.DENY ? "mb-2" : "mb-0"}
        >
          <Radio.Group
            value={data.actionType}
            onChange={(e) => data.onActionTypeChange?.(e.target.value)}
            optionType="button"
            buttonStyle="solid"
            options={ACTION_TYPE_OPTIONS}
            className="w-full"
          />
        </Form.Item>
        {data.actionType === ActionType.DENY && (
          <Form.Item label="Denial message" className="mb-0">
            <Input.TextArea
              placeholder="Message shown when access is blocked"
              value={data.actionMessage}
              onChange={(e) => data.onActionMessageChange?.(e.target.value)}
              autoSize={{ minRows: 1, maxRows: 3 }}
              data-testid="action-message-input"
            />
          </Form.Item>
        )}
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
