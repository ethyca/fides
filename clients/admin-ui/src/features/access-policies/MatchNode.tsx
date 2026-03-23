import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import {
  Avatar,
  Button,
  Flex,
  Form,
  Icons,
  Popconfirm,
  Select,
  Text,
} from "fidesui";

import DataCategorySelect from "~/features/common/dropdown/DataCategorySelect";
import DataSubjectSelect from "~/features/common/dropdown/DataSubjectSelect";
import DataUseSelect from "~/features/common/dropdown/DataUseSelect";

import styles from "./MatchNode.module.scss";
import {
  CONDITION_OPERATOR_OPTIONS,
  CONDITION_PROPERTY_OPTIONS,
} from "./constants";
import NodeActions from "./NodeActions";
import { ConditionOperator, ConditionProperty } from "./types";

export interface ConditionNodeData extends Record<string, unknown> {
  property?: ConditionProperty;
  values?: string[];
  operator?: ConditionOperator;
  onPropertyChange?: (value: ConditionProperty) => void;
  onValuesChange?: (values: string[]) => void;
  onOperatorChange?: (value: ConditionOperator) => void;
  onAddNode?: () => void;
  onAddCondition?: () => void;
  onAddConstraint?: () => void;
  onDelete?: () => void;
  hasChildren?: boolean;
  isFirstOfType?: boolean;
}

export type ConditionNodeType = Node<ConditionNodeData, "conditionNode">;

const ConditionNode = ({ data }: NodeProps<ConditionNodeType>) => (
  <div className={styles.node} data-testid="condition-node">
    <Handle
      type="target"
      position={Position.Left}
      id="left"
      className={styles.handle}
    />
    {!data.isFirstOfType && (
      <Handle
        type="target"
        position={Position.Top}
        id="top"
        className={styles.handle}
      />
    )}
    <Flex align="center" gap="small" className={styles.header}>
      <Avatar
        shape="square"
        size="small"
        icon={<Icons.SettingsAdjust size={16} />}
        className={styles.avatar}
      />
      <Text strong style={{ flex: 1 }}>
        Match
      </Text>
      <Popconfirm
        title="Delete match"
        description="Are you sure you want to delete this match and its children?"
        onConfirm={data.onDelete}
        okText="Delete"
        okButtonProps={{ danger: true }}
        cancelText="Cancel"
      >
        <Button
          type="text"
          size="small"
          icon={<Icons.TrashCan size={14} />}
          danger
          className="nodrag"
          aria-label="Delete match"
          data-testid="delete-condition-btn"
        />
      </Popconfirm>
    </Flex>
    <div className={styles.body}>
      <Form layout="vertical" className="nodrag">
        <Form.Item label="Taxonomy" className="mb-2">
          <Select
            placeholder="Select taxonomy"
            value={data.property}
            onChange={(value) => data.onPropertyChange?.(value)}
            options={CONDITION_PROPERTY_OPTIONS}
            variant="outlined"
            className="w-full"
            aria-label="Select taxonomy"
            data-testid="condition-property-select"
          />
        </Form.Item>
        <Form.Item label="Match" className="mb-2">
          <Select
            placeholder="Select match type"
            value={data.operator}
            onChange={(value) => data.onOperatorChange?.(value)}
            options={CONDITION_OPERATOR_OPTIONS}
            variant="outlined"
            className="w-full"
            aria-label="Select match type"
            data-testid="condition-operator-select"
          />
        </Form.Item>
        <Form.Item label="Values" className="mb-0">
          {data.property === ConditionProperty.DATA_USE && (
            <DataUseSelect
              selectedTaxonomies={data.values}
              value={data.values}
              onChange={(values) => data.onValuesChange?.(values as string[])}
              mode="multiple"
              maxTagCount={1}
              placeholder="Select data uses"
              data-testid="condition-values-data-use"
            />
          )}
          {data.property === ConditionProperty.DATA_CATEGORIES && (
            <DataCategorySelect
              selectedTaxonomies={data.values}
              value={data.values}
              onChange={(values) => data.onValuesChange?.(values as string[])}
              mode="multiple"
              maxTagCount={1}
              placeholder="Select data categories"
              data-testid="condition-values-data-category"
            />
          )}
          {data.property === ConditionProperty.DATA_SUBJECTS && (
            <DataSubjectSelect
              selectedTaxonomies={data.values}
              value={data.values}
              onChange={(values) => data.onValuesChange?.(values as string[])}
              mode="multiple"
              maxTagCount={1}
              placeholder="Select data subjects"
              data-testid="condition-values-data-subject"
            />
          )}
          {!data.property && (
            <Select
              disabled
              placeholder="Select a taxonomy first"
              className="w-full"
              aria-label="Select values"
              data-testid="condition-values-disabled"
            />
          )}
        </Form.Item>
      </Form>
    </div>
    <div className={styles.addSiblingRow}>
      <Button
        type="text"
        size="small"
        icon={<Icons.Add size={14} />}
        onClick={data.onAddCondition}
        aria-label="Add match"
        data-testid="add-sibling-condition-btn"
        className={styles.addSiblingButton}
      >
        Match
      </Button>
    </div>
    {!data.hasChildren && (
      <NodeActions
        onAddNode={data.onAddNode}
        onAddConstraint={data.onAddConstraint}
        showAddCondition={false}
        showAddAction={false}
      />
    )}
    <Handle
      type="source"
      position={Position.Right}
      id="right"
      className={styles.handle}
    />
    <Handle
      type="source"
      position={Position.Bottom}
      id="bottom"
      className={styles.handle}
    />
  </div>
);

export default ConditionNode;
