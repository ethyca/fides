import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import {
  Avatar,
  Collapse,
  Flex,
  Form,
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
  control: string | null;
  controlOptions: NonNullable<SelectProps["options"]>;
  actionMessage: string;
  onNameChange: (value: string) => void;
  onDescriptionChange: (value: string) => void;
  onFidesKeyChange: (value: string) => void;
  onEnabledChange: (value: boolean) => void;
  onPriorityChange: (value: number) => void;
  onControlChange: (value: string | null) => void;
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
    control,
    controlOptions,
    onNameChange,
    onDescriptionChange,
    onFidesKeyChange,
    onEnabledChange,
    onPriorityChange,
    onControlChange,
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
      <div className={styles.body}>
        <Form layout="vertical" className="nodrag">
          <Form.Item label="Name" className="mb-2">
            <Input
              placeholder="Enter name"
              value={name}
              onChange={(e) => onNameChange(e.target.value)}
              data-testid="policy-name-input"
            />
          </Form.Item>
          <Form.Item label="Description" className="mb-2">
            <Input.TextArea
              placeholder="Policy description"
              value={description}
              onChange={(e) => onDescriptionChange(e.target.value)}
              autoSize={{ minRows: 2, maxRows: 4 }}
              data-testid="policy-description-input"
            />
          </Form.Item>
          <Form.Item label="Control" className="mb-2">
            <Select
              placeholder="Select control"
              value={control ?? undefined}
              onChange={(value) => onControlChange(value ?? null)}
              options={controlOptions}
              className="w-full"
              allowClear
              data-testid="policy-control-select"
              aria-label="Select control"
            />
          </Form.Item>
        </Form>
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
                <Form layout="vertical">
                  <Form.Item label="Policy key" className="mb-2">
                    <Input
                      placeholder="Unique identifier"
                      value={fidesKey}
                      onChange={(e) => onFidesKeyChange(e.target.value)}
                      data-testid="policy-fides-key-input"
                    />
                  </Form.Item>
                  <Form.Item label="Priority" className="mb-0">
                    <InputNumber
                      value={priority}
                      onChange={(val) => onPriorityChange(val ?? 0)}
                      min={0}
                      className="w-full"
                      data-testid="policy-priority-input"
                    />
                  </Form.Item>
                </Form>
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
