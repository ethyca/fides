import { Flex, Form, Input, Select, Tag, Typography } from "fidesui";

import { ActionType, RuleResponseWithTargets, RuleTarget } from "~/types/api";

const { Text } = Typography;

const actionTypeOptions = [
  { value: ActionType.ACCESS, label: "Access" },
  { value: ActionType.ERASURE, label: "Erasure" },
  { value: ActionType.CONSENT, label: "Consent" },
  { value: ActionType.UPDATE, label: "Update" },
];

const maskingStrategyOptions = [
  { value: "null_rewrite", label: "Null Rewrite" },
  { value: "string_rewrite", label: "String Rewrite" },
  { value: "hash", label: "Hash" },
  { value: "random_string_rewrite", label: "Random String Rewrite" },
  { value: "aes_encrypt", label: "AES Encrypt" },
  { value: "hmac", label: "HMAC" },
];

interface RulePanelProps {
  rule: RuleResponseWithTargets;
}

const RulePanel = ({ rule }: RulePanelProps) => {
  const isAccessRule = rule.action_type === ActionType.ACCESS;
  const isErasureRule = rule.action_type === ActionType.ERASURE;

  return (
    <div className="py-2">
      <Form layout="vertical" disabled>
        <div className="max-w-md">
          <Form.Item label="Rule name">
            <Input
              value={rule.name}
              disabled
              data-testid={`rule-name-${rule.key}`}
            />
          </Form.Item>

          <Form.Item label="Rule key">
            <Input
              value={rule.key ?? ""}
              disabled
              className="font-mono"
              data-testid={`rule-key-${rule.key}`}
            />
          </Form.Item>

          <Form.Item label="Action">
            {/* eslint-disable-next-line jsx-a11y/control-has-associated-label */}
            <Select
              value={rule.action_type}
              options={actionTypeOptions}
              disabled
              data-testid={`rule-action-${rule.key}`}
            />
          </Form.Item>

          {isErasureRule && (
            <Form.Item label="Masking strategy">
              {/* eslint-disable-next-line jsx-a11y/control-has-associated-label */}
              <Select
                value={rule.masking_strategy?.strategy}
                options={maskingStrategyOptions}
                placeholder="No masking strategy"
                disabled
                data-testid={`rule-masking-${rule.key}`}
              />
            </Form.Item>
          )}

          {isAccessRule && (
            <Form.Item label="Storage destination">
              <Input
                value={
                  rule.storage_destination?.name ?? "No storage destination"
                }
                disabled
                data-testid={`rule-storage-${rule.key}`}
              />
            </Form.Item>
          )}

          <Form.Item label="Data category targets">
            <Flex vertical style={{ width: "100%" }}>
              <Input
                placeholder="Data categories"
                disabled
                data-testid={`rule-targets-input-${rule.key}`}
              />
              {rule.targets && rule.targets.length > 0 ? (
                <Flex wrap="wrap" gap={8} className="mt-2">
                  {rule.targets.map((target: RuleTarget) => (
                    <Tag
                      key={target.key ?? target.data_category}
                      color="default"
                    >
                      {target.data_category}
                    </Tag>
                  ))}
                </Flex>
              ) : (
                <div className="mt-2">
                  <Text type="secondary">No targets configured</Text>
                </div>
              )}
            </Flex>
          </Form.Item>
        </div>
      </Form>
    </div>
  );
};

export default RulePanel;
