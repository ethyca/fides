import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import {
  Avatar,
  Collapse,
  Flex,
  Icons,
  Input,
  InputNumber,
  Select,
  SelectProps,
  Switch,
  Text,
} from "fidesui";

import NodeActions from "./NodeActions";
import styles from "./PolicyNode.module.scss";

export interface PolicyNodeData extends Record<string, unknown> {
  name: string;
  description: string;
  fidesKey: string;
  enabled: boolean;
  priority: number;
  controls: string[];
  controlOptions: NonNullable<SelectProps["options"]>;
  actionMessage: string;
  onNameChange: (value: string) => void;
  onDescriptionChange: (value: string) => void;
  onFidesKeyChange: (value: string) => void;
  onEnabledChange: (value: boolean) => void;
  onPriorityChange: (value: number) => void;
  onControlsChange: (value: string[]) => void;
  onActionMessageChange: (value: string) => void;
  onAddNode?: () => void;
  onAddAction?: () => void;
  hasChildren?: boolean;
}

export type PolicyNodeType = Node<PolicyNodeData, "policyNode">;

const PolicyNode = ({ data }: NodeProps<PolicyNodeType>) => {
  const {
    name,
    description,
    fidesKey,
    enabled,
    priority,
    controls,
    controlOptions,
    onNameChange,
    onDescriptionChange,
    onFidesKeyChange,
    onEnabledChange,
    onPriorityChange,
    onControlsChange,
    onAddNode,
    onAddAction,
    hasChildren,
  } = data;

  return (
    <div className={styles.node} data-testid="policy-node">
      <Flex align="center" gap="small" className={styles.header}>
        <Avatar
          shape="square"
          size="small"
          icon={<Icons.DocumentBlank size={16} />}
          className={styles.avatar}
        />
        <Text strong style={{ flex: 1 }}>
          Policy
        </Text>
        <Flex align="center" gap={4} className="nodrag">
          <Text type="secondary" style={{ fontSize: 12 }}>
            Enabled
          </Text>
          <Switch
            size="small"
            checked={enabled}
            onChange={onEnabledChange}
            data-testid="policy-enabled-toggle"
          />
        </Flex>
      </Flex>
      <Input
        placeholder="Enter name"
        value={name}
        onChange={(e) => onNameChange(e.target.value)}
        variant="borderless"
        className={styles.field}
        data-testid="policy-name-input"
      />
      <Input
        placeholder="Policy description"
        value={description}
        onChange={(e) => onDescriptionChange(e.target.value)}
        variant="borderless"
        className={styles.field}
        data-testid="policy-description-input"
      />
      <Select
        placeholder="Select controls"
        mode="multiple"
        value={controls}
        onChange={onControlsChange}
        options={controlOptions}
        variant="borderless"
        className={styles.selectField}
        data-testid="policy-controls-select"
        aria-label="Select controls"
      />
      <div className="nodrag">
        <Collapse
          size="small"
          ghost
          items={[
            {
              key: "advanced",
              label: (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  Advanced
                </Text>
              ),
              children: (
                <>
                  <Input
                    placeholder="Fides key (unique identifier)"
                    value={fidesKey}
                    onChange={(e) => onFidesKeyChange(e.target.value)}
                    size="small"
                    className={styles.field}
                    data-testid="policy-fides-key-input"
                  />
                  <Flex gap="small" align="center" className={styles.field}>
                    <Text
                      type="secondary"
                      style={{ fontSize: 12, whiteSpace: "nowrap" }}
                    >
                      Priority
                    </Text>
                    <InputNumber
                      value={priority}
                      onChange={(val) => onPriorityChange(val ?? 0)}
                      min={0}
                      size="small"
                      style={{ width: 80 }}
                      data-testid="policy-priority-input"
                    />
                  </Flex>
                </>
              ),
            },
          ]}
        />
      </div>
      {!hasChildren && (
        <NodeActions
          onAddNode={onAddNode}
          onAddAction={onAddAction}
          showAddCondition={false}
          showAddConstraint={false}
        />
      )}
      <Handle
        type="source"
        position={Position.Right}
        className={styles.handle}
      />
    </div>
  );
};

export default PolicyNode;
