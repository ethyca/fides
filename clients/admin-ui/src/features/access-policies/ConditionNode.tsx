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

import styles from "./ConditionNode.module.scss";
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
}

export type ConditionNodeType = Node<ConditionNodeData, "conditionNode">;

const ConditionNode = ({ data }: NodeProps<ConditionNodeType>) => {
  const showOperator = (data.values?.length ?? 0) >= 2;

  return (
    <div className={styles.node} data-testid="condition-node">
      <Handle
        type="target"
        position={Position.Left}
        className={styles.handle}
      />
      <Flex align="center" gap="small" className={styles.header}>
        <Avatar
          shape="square"
          size="small"
          icon={<Icons.SettingsAdjust size={16} />}
          className={styles.avatar}
        />
        <Text strong style={{ flex: 1 }}>
          Condition
        </Text>
        <Popconfirm
          title="Delete condition"
          description="Are you sure you want to delete this condition and its children?"
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
            aria-label="Delete condition"
            data-testid="delete-condition-btn"
          />
        </Popconfirm>
      </Flex>
      <div className={styles.body}>
        <Form layout="vertical" className="nodrag">
          <Form.Item label="Property" className="mb-2">
            <Select
              placeholder="Select property"
              value={data.property}
              onChange={(value) => data.onPropertyChange?.(value)}
              options={CONDITION_PROPERTY_OPTIONS}
              variant="outlined"
              className="w-full"
              aria-label="Select condition property"
              data-testid="condition-property-select"
            />
          </Form.Item>
          {data.property && (
            <Form.Item label="Values" className="mb-2">
              {data.property === ConditionProperty.DATA_USE && (
                <DataUseSelect
                  selectedTaxonomies={data.values}
                  value={data.values}
                  onChange={(values) =>
                    data.onValuesChange?.(values as string[])
                  }
                  mode="multiple"
                  placeholder="Select data uses"
                  data-testid="condition-values-data-use"
                />
              )}
              {data.property === ConditionProperty.DATA_CATEGORIES && (
                <DataCategorySelect
                  selectedTaxonomies={data.values}
                  value={data.values}
                  onChange={(values) =>
                    data.onValuesChange?.(values as string[])
                  }
                  mode="multiple"
                  placeholder="Select data categories"
                  data-testid="condition-values-data-category"
                />
              )}
              {data.property === ConditionProperty.DATA_SUBJECTS && (
                <DataSubjectSelect
                  selectedTaxonomies={data.values}
                  value={data.values}
                  onChange={(values) =>
                    data.onValuesChange?.(values as string[])
                  }
                  mode="multiple"
                  placeholder="Select data subjects"
                  data-testid="condition-values-data-subject"
                />
              )}
            </Form.Item>
          )}
          {showOperator && (
            <Form.Item label="Operator" className="mb-0">
              <Select
                placeholder="Select operator"
                value={data.operator}
                onChange={(value) => data.onOperatorChange?.(value)}
                options={CONDITION_OPERATOR_OPTIONS}
                variant="outlined"
                className="w-full"
                aria-label="Select condition operator"
                data-testid="condition-operator-select"
              />
            </Form.Item>
          )}
        </Form>
      </div>
      {!data.hasChildren && (
        <NodeActions
          onAddNode={data.onAddNode}
          onAddCondition={data.onAddCondition}
          onAddConstraint={data.onAddConstraint}
          showAddAction={false}
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

export default ConditionNode;
