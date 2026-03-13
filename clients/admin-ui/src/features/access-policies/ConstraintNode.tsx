import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import { Avatar, Flex, Form, Icons, Input, Radio, Select, Text } from "fidesui";

import {
  CONSENT_VALUE_OPTIONS,
  CONSTRAINT_TYPE_OPTIONS,
  USER_OPERATOR_OPTIONS,
} from "./constants";
import styles from "./ConstraintNode.module.scss";
import { ConsentValue, ConstraintType, UserOperator } from "./types";

export interface ConstraintNodeData extends Record<string, unknown> {
  constraintType?: ConstraintType;
  preferenceKey?: string;
  consentValue?: ConsentValue;
  userKey?: string;
  userValue?: string;
  userOperator?: UserOperator;
  onConstraintTypeChange?: (value: ConstraintType) => void;
  onPreferenceKeyChange?: (value: string) => void;
  onConsentValueChange?: (value: ConsentValue) => void;
  onUserKeyChange?: (value: string) => void;
  onUserValueChange?: (value: string) => void;
  onUserOperatorChange?: (value: UserOperator) => void;
}

export type ConstraintNodeType = Node<ConstraintNodeData, "constraintNode">;

const ConstraintNode = ({ data }: NodeProps<ConstraintNodeType>) => (
  <div className={styles.node} data-testid="constraint-node">
    <Handle type="target" position={Position.Left} className={styles.handle} />
    <Flex align="center" gap="small" className={styles.header}>
      <Avatar
        shape="square"
        size="small"
        icon={<Icons.Locked size={16} />}
        className={styles.avatar}
      />
      <Text strong>Constraint</Text>
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
          />
        </Form.Item>
        {data.constraintType === ConstraintType.CONSENT && (
          <>
            <Form.Item label="Preference key" className="mb-2">
              <Input
                placeholder="Enter preference key"
                value={data.preferenceKey}
                onChange={(e) => data.onPreferenceKeyChange?.(e.target.value)}
                data-testid="constraint-preference-key"
              />
            </Form.Item>
            <Form.Item label="Consent value" className="mb-0">
              <Select
                placeholder="Select consent value"
                value={data.consentValue}
                onChange={(value) => data.onConsentValueChange?.(value)}
                options={CONSENT_VALUE_OPTIONS}
                className="w-full"
                aria-label="Select consent value"
                data-testid="constraint-consent-value"
              />
            </Form.Item>
          </>
        )}
        {data.constraintType === ConstraintType.USER && (
          <>
            <Form.Item label="Key" className="mb-2">
              <Input
                placeholder="Enter key"
                value={data.userKey}
                onChange={(e) => data.onUserKeyChange?.(e.target.value)}
                data-testid="constraint-user-key"
              />
            </Form.Item>
            <Form.Item label="Value" className="mb-2">
              <Input
                placeholder="Enter value"
                value={data.userValue}
                onChange={(e) => data.onUserValueChange?.(e.target.value)}
                data-testid="constraint-user-value"
              />
            </Form.Item>
            <Form.Item label="Operator" className="mb-0">
              <Select
                placeholder="Select operator"
                value={data.userOperator}
                onChange={(value) => data.onUserOperatorChange?.(value)}
                options={USER_OPERATOR_OPTIONS}
                className="w-full"
                aria-label="Select user operator"
                data-testid="constraint-user-operator"
              />
            </Form.Item>
          </>
        )}
      </Form>
    </div>
    <Handle type="source" position={Position.Right} className={styles.handle} />
  </div>
);

export default ConstraintNode;
