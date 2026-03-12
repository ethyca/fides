import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import { Avatar, Flex, Icons, Input, Select, SelectProps, Text } from "fidesui";

import styles from "./PolicyNode.module.scss";

export interface PolicyNodeData extends Record<string, unknown> {
  name: string;
  description: string;
  controlGroup?: string;
  controlGroupOptions: NonNullable<SelectProps["options"]>;
  onNameChange: (value: string) => void;
  onDescriptionChange: (value: string) => void;
  onControlGroupChange: (value: string | undefined) => void;
}

export type PolicyNodeType = Node<PolicyNodeData, "policyNode">;

const PolicyNode = ({ data }: NodeProps<PolicyNodeType>) => {
  const {
    name,
    description,
    controlGroup,
    controlGroupOptions,
    onNameChange,
    onDescriptionChange,
    onControlGroupChange,
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
        <Text strong>Policy</Text>
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
        placeholder="Select control group"
        value={controlGroup}
        onChange={onControlGroupChange}
        options={controlGroupOptions}
        variant="borderless"
        className={styles.field}
        data-testid="policy-control-group-select"
        aria-label="Select control group"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className={styles.handle}
      />
    </div>
  );
};

export default PolicyNode;
