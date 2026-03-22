import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import {
  Avatar,
  Button,
  Flex,
  Form,
  Icons,
  Input,
  Popconfirm,
  Radio,
  Select,
  Text,
} from "fidesui";

import {
  CONSENT_REQUIREMENT_OPTIONS,
  CONSTRAINT_TYPE_OPTIONS,
  DATA_FLOW_DIRECTION_OPTIONS,
  DATA_FLOW_OPERATOR_OPTIONS,
  GEO_OPERATOR_OPTIONS,
} from "./constants";
import styles from "./ConstraintNode.module.scss";
import {
  ConsentRequirement,
  ConstraintType,
  DataFlowDirection,
  DataFlowOperator,
  GeoOperator,
} from "./types";

export interface ConstraintNodeData extends Record<string, unknown> {
  constraintType?: ConstraintType;
  // Consent fields
  privacyNoticeKey?: string;
  consentRequirement?: ConsentRequirement;
  // Geo location fields
  geoField?: string;
  geoOperator?: GeoOperator;
  geoValues?: string[];
  // Data flow fields
  dataFlowDirection?: DataFlowDirection;
  dataFlowOperator?: DataFlowOperator;
  dataFlowSystems?: string[];
  // Callbacks
  onConstraintTypeChange?: (value: ConstraintType) => void;
  onPrivacyNoticeKeyChange?: (value: string) => void;
  onConsentRequirementChange?: (value: ConsentRequirement) => void;
  onGeoFieldChange?: (value: string) => void;
  onGeoOperatorChange?: (value: GeoOperator) => void;
  onGeoValuesChange?: (value: string[]) => void;
  onDataFlowDirectionChange?: (value: DataFlowDirection) => void;
  onDataFlowOperatorChange?: (value: DataFlowOperator) => void;
  onDataFlowSystemsChange?: (value: string[]) => void;
  onDelete?: () => void;
  onAddConstraint?: () => void;
}

export type ConstraintNodeType = Node<ConstraintNodeData, "constraintNode">;

const TagInput = ({
  value = [],
  onChange,
  placeholder,
  testId,
}: {
  value?: string[];
  onChange?: (values: string[]) => void;
  placeholder: string;
  testId: string;
}) => (
  <Select
    mode="tags"
    value={value}
    onChange={onChange}
    placeholder={placeholder}
    className="w-full"
    tokenSeparators={[","]}
    data-testid={testId}
    aria-label={placeholder}
  />
);

const ConstraintNode = ({ data }: NodeProps<ConstraintNodeType>) => (
  <div className={styles.node} data-testid="constraint-node">
    <Handle
      type="target"
      position={Position.Left}
      id="left"
      className={styles.handle}
    />
    <Handle
      type="target"
      position={Position.Top}
      id="top"
      className={styles.handle}
    />
    <Flex align="center" gap="small" className={styles.header}>
      <Avatar
        shape="square"
        size="small"
        icon={<Icons.Locked size={16} />}
        className={styles.avatar}
      />
      <Text strong style={{ flex: 1 }}>
        Constraint
      </Text>
      <Popconfirm
        title="Delete constraint"
        description="Are you sure you want to delete this constraint?"
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
          aria-label="Delete constraint"
          data-testid="delete-constraint-btn"
        />
      </Popconfirm>
    </Flex>
    <div className={styles.body}>
      <Form layout="vertical" className="nodrag">
        <Form.Item label="Type" className="mb-2">
          <Radio.Group
            value={data.constraintType}
            onChange={(e) => data.onConstraintTypeChange?.(e.target.value)}
            optionType="button"
            buttonStyle="solid"
            options={CONSTRAINT_TYPE_OPTIONS}
            size="small"
          />
        </Form.Item>

        {/* Consent fields */}
        {data.constraintType === ConstraintType.CONSENT && (
          <>
            <Form.Item label="Privacy notice key" className="mb-2">
              <Input
                placeholder="Enter privacy notice key"
                value={data.privacyNoticeKey}
                onChange={(e) =>
                  data.onPrivacyNoticeKeyChange?.(e.target.value)
                }
                data-testid="constraint-privacy-notice-key"
              />
            </Form.Item>
            <Form.Item label="Requirement" className="mb-0">
              <Select
                placeholder="Select requirement"
                value={data.consentRequirement}
                onChange={(value) =>
                  data.onConsentRequirementChange?.(value)
                }
                options={CONSENT_REQUIREMENT_OPTIONS}
                className="w-full"
                aria-label="Select consent requirement"
                data-testid="constraint-consent-requirement"
              />
            </Form.Item>
          </>
        )}

        {/* Geo location fields */}
        {data.constraintType === ConstraintType.GEO_LOCATION && (
          <>
            <Form.Item label="Field" className="mb-2">
              <Input
                placeholder="e.g. environment.geo_location"
                value={data.geoField}
                onChange={(e) => data.onGeoFieldChange?.(e.target.value)}
                data-testid="constraint-geo-field"
              />
            </Form.Item>
            <Form.Item label="Operator" className="mb-2">
              <Select
                value={data.geoOperator}
                onChange={(value) => data.onGeoOperatorChange?.(value)}
                options={GEO_OPERATOR_OPTIONS}
                className="w-full"
                aria-label="Select geo operator"
                data-testid="constraint-geo-operator"
              />
            </Form.Item>
            <Form.Item label="Values (ISO codes)" className="mb-0">
              <TagInput
                value={data.geoValues}
                onChange={data.onGeoValuesChange}
                placeholder="e.g. US-CA, EU"
                testId="constraint-geo-values"
              />
            </Form.Item>
          </>
        )}

        {/* Data flow fields */}
        {data.constraintType === ConstraintType.DATA_FLOW && (
          <>
            <Form.Item label="Direction" className="mb-2">
              <Select
                value={data.dataFlowDirection}
                onChange={(value) =>
                  data.onDataFlowDirectionChange?.(value)
                }
                options={DATA_FLOW_DIRECTION_OPTIONS}
                className="w-full"
                aria-label="Select data flow direction"
                data-testid="constraint-data-flow-direction"
              />
            </Form.Item>
            <Form.Item label="Operator" className="mb-2">
              <Select
                value={data.dataFlowOperator}
                onChange={(value) =>
                  data.onDataFlowOperatorChange?.(value)
                }
                options={DATA_FLOW_OPERATOR_OPTIONS}
                className="w-full"
                aria-label="Select data flow operator"
                data-testid="constraint-data-flow-operator"
              />
            </Form.Item>
            <Form.Item label="Systems" className="mb-0">
              <TagInput
                value={data.dataFlowSystems}
                onChange={data.onDataFlowSystemsChange}
                placeholder="Enter system fides keys"
                testId="constraint-data-flow-systems"
              />
            </Form.Item>
          </>
        )}
      </Form>
    </div>
    <div className={styles.addSiblingRow}>
      <Button
        type="text"
        size="small"
        icon={<Icons.Add size={14} />}
        onClick={data.onAddConstraint}
        aria-label="Add constraint"
        data-testid="add-sibling-constraint-btn"
        className={styles.addSiblingButton}
      >
        Constraint
      </Button>
    </div>
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

export default ConstraintNode;
