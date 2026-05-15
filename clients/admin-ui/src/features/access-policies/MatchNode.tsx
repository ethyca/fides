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
import SystemGroupSelect from "~/features/common/dropdown/SystemGroupSelect";
import CustomTaxonomySelect from "~/features/taxonomy/components/CustomTaxonomySelect";

import { CONDITION_OPERATOR_OPTIONS } from "./constants";
import { usePolicyTaxonomyOptions } from "./hooks/usePolicyTaxonomyOptions";
import styles from "./MatchNode.module.scss";
import NodeActions from "./NodeActions";
import { ConditionOperator, ConditionProperty } from "./types";

export interface ConditionNodeData extends Record<string, unknown> {
  property?: string;
  values?: string[];
  operator?: ConditionOperator;
  /** Taxonomy keys already used by sibling condition nodes — disabled in the dropdown. */
  disabledProperties?: string[];
  onPropertyChange?: (value: string) => void;
  onValuesChange?: (values: string[]) => void;
  onOperatorChange?: (value: ConditionOperator) => void;
  onAddNode?: () => void;
  onAddCondition?: () => void;
  onAddConstraint?: () => void;
  onDelete?: () => void;
  hasChildren?: boolean;
  isFirstOfType?: boolean;
  isLastOfType?: boolean;
}

export type ConditionNodeType = Node<ConditionNodeData, "conditionNode">;

const renderValuesSelect = (
  property: string | undefined,
  values: string[] | undefined,
  onChange: (values: string[]) => void,
) => {
  if (!property) {
    return (
      <Select
        disabled
        placeholder="Select a taxonomy first"
        className="w-full"
        aria-label="Select values"
        data-testid="condition-values-disabled"
      />
    );
  }

  const commonProps = {
    selectedTaxonomies: values,
    value: values,
    onChange: (v: unknown) => onChange(v as string[]),
    mode: "multiple" as const,
    maxTagCount: 1 as const,
  };

  switch (property) {
    case ConditionProperty.DATA_USE:
      return (
        <DataUseSelect
          {...commonProps}
          placeholder="Select data uses"
          data-testid="condition-values-data-use"
        />
      );
    case ConditionProperty.DATA_CATEGORIES:
      return (
        <DataCategorySelect
          {...commonProps}
          placeholder="Select data categories"
          data-testid="condition-values-data-category"
        />
      );
    case ConditionProperty.DATA_SUBJECTS:
      return (
        <DataSubjectSelect
          {...commonProps}
          placeholder="Select data subjects"
          data-testid="condition-values-data-subject"
        />
      );
    case ConditionProperty.SYSTEM_GROUP:
      return (
        <SystemGroupSelect
          {...commonProps}
          placeholder="Select system groups"
          data-testid="condition-values-system-group"
        />
      );
    default:
      return (
        <CustomTaxonomySelect
          {...commonProps}
          taxonomyKey={property}
          placeholder="Select values"
          data-testid="condition-values-custom"
        />
      );
  }
};

const ConditionNode = ({ data }: NodeProps<ConditionNodeType>) => {
  const { options, labelByKey } = usePolicyTaxonomyOptions();

  const disabledSet = new Set(data.disabledProperties ?? []);
  const propertyOptions = options.map((opt) => ({
    value: opt.value,
    label: opt.label,
    disabled: disabledSet.has(opt.value) && opt.value !== data.property,
  }));

  const valuesLabel = data.property
    ? (labelByKey[data.property] ?? data.property)
    : "Values";

  return (
    <div className={styles.node} data-testid="condition-node">
      {data.isFirstOfType && (
        <Handle
          type="target"
          position={Position.Left}
          id="left"
          className={styles.handle}
        />
      )}
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
              options={propertyOptions}
              variant="outlined"
              className="w-full"
              aria-label="Select taxonomy"
              data-testid="condition-property-select"
            />
          </Form.Item>
          <Form.Item label="Match" className="mb-2">
            <Select
              placeholder="Select match type"
              value={data.operator ?? ConditionOperator.ALL}
              onChange={(value) => data.onOperatorChange?.(value)}
              options={CONDITION_OPERATOR_OPTIONS}
              variant="outlined"
              className="w-full"
              aria-label="Select match type"
              data-testid="condition-operator-select"
            />
          </Form.Item>
          <Form.Item label={valuesLabel} className="mb-0">
            {renderValuesSelect(data.property, data.values, (values) =>
              data.onValuesChange?.(values),
            )}
          </Form.Item>
        </Form>
      </div>
      {data.isFirstOfType && !data.hasChildren && (
        <NodeActions
          onAddNode={data.onAddNode}
          onAddConstraint={data.onAddConstraint}
          showAddCondition={false}
          showAddAction={false}
        />
      )}
      {data.isLastOfType && (
        <NodeActions
          position="bottom"
          onAddNode={data.onAddCondition}
          onAddCondition={data.onAddCondition}
          showAddAction={false}
          showAddConstraint={false}
        />
      )}
      {data.isFirstOfType && (
        <Handle
          type="source"
          position={Position.Right}
          id="right"
          className={styles.handle}
        />
      )}
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom"
        className={styles.handle}
      />
    </div>
  );
};

export default ConditionNode;
