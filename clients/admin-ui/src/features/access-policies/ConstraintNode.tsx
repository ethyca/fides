import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import {
  Avatar,
  Button,
  Flex,
  Form,
  Icons,
  LocationSelect,
  Popconfirm,
  Radio,
  Select,
  Text,
} from "fidesui";

import { SystemSelect } from "~/features/common/dropdown/SystemSelect";

import {
  CONSENT_REQUIREMENT_OPTIONS,
  CONSTRAINT_TYPE_OPTIONS,
  DATA_FLOW_DIRECTION_OPTIONS,
  DATA_FLOW_OPERATOR_OPTIONS,
  GEO_OPERATOR_OPTIONS,
} from "./constants";
import styles from "./ConstraintNode.module.scss";
import NodeActions from "./NodeActions";
import PrivacyNoticeSelect from "./PrivacyNoticeSelect";
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
  isFirstOfType?: boolean;
  isLastOfType?: boolean;
}

export type ConstraintNodeType = Node<ConstraintNodeData, "constraintNode">;

const ConstraintNode = ({ data }: NodeProps<ConstraintNodeType>) => (
  <div className={styles.node} data-testid="constraint-node">
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
            <Form.Item label="Privacy notice" className="mb-2">
              <PrivacyNoticeSelect
                value={data.privacyNoticeKey}
                onChange={(value) => data.onPrivacyNoticeKeyChange?.(value)}
                className="w-full"
                data-testid="constraint-privacy-notice-key"
              />
            </Form.Item>
            <Form.Item label="Requirement" className="mb-0">
              <Select
                placeholder="Select requirement"
                value={data.consentRequirement}
                onChange={(value) => data.onConsentRequirementChange?.(value)}
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
            <Form.Item label="Locations" className="mb-0">
              <LocationSelect
                mode="multiple"
                value={data.geoValues}
                onChange={(values) =>
                  data.onGeoValuesChange?.(values as string[])
                }
                includeCountryOnlyOptions
                maxTagCount={1}
                data-testid="constraint-geo-values"
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
                onChange={(value) => data.onDataFlowDirectionChange?.(value)}
                options={DATA_FLOW_DIRECTION_OPTIONS}
                className="w-full"
                aria-label="Select data flow direction"
                data-testid="constraint-data-flow-direction"
              />
            </Form.Item>
            <Form.Item label="Operator" className="mb-2">
              <Select
                value={data.dataFlowOperator}
                onChange={(value) => data.onDataFlowOperatorChange?.(value)}
                options={DATA_FLOW_OPERATOR_OPTIONS}
                className="w-full"
                aria-label="Select data flow operator"
                data-testid="constraint-data-flow-operator"
              />
            </Form.Item>
            <Form.Item label="Systems" className="mb-0">
              <SystemSelect
                mode="multiple"
                value={data.dataFlowSystems}
                onChange={(values) =>
                  data.onDataFlowSystemsChange?.(values as string[])
                }
                maxTagCount={1}
                data-testid="constraint-data-flow-systems"
              />
            </Form.Item>
          </>
        )}
      </Form>
    </div>
    {data.isLastOfType && (
      <NodeActions
        position="bottom"
        onAddNode={data.onAddConstraint}
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

export default ConstraintNode;
