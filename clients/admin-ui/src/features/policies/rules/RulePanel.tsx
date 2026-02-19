import { Flex, Form, Input, Select, Typography } from "fidesui";
import { useMemo } from "react";

import { InfoPopover } from "~/features/common/InfoPopover";
import { formatMaskingStrategyName } from "~/features/policies/utils/formatMaskingStrategyName";
import { useGetMaskingStrategiesQuery } from "~/features/policy/policy.slice";
import { ActionType, RuleResponse } from "~/types/api";

const { Text } = Typography;

const actionTypeOptions = [
  { value: ActionType.ACCESS, label: "Access" },
  { value: ActionType.ERASURE, label: "Erasure" },
  { value: ActionType.CONSENT, label: "Consent" },
  { value: ActionType.UPDATE, label: "Update" },
];

interface RulePanelProps {
  rule: RuleResponse;
}

const RulePanel = ({ rule }: RulePanelProps) => {
  const isAccessRule = rule.action_type === ActionType.ACCESS;
  const isErasureRule = rule.action_type === ActionType.ERASURE;

  const { data: strategies } = useGetMaskingStrategiesQuery(undefined, {
    skip: !isErasureRule,
  });

  const maskingStrategyOptions = useMemo(
    () =>
      (strategies ?? []).map((s) => ({
        value: s.name,
        label: formatMaskingStrategyName(s.name),
      })),
    [strategies],
  );

  const currentStrategyDescription = useMemo(() => {
    if (!strategies || !rule.masking_strategy?.strategy) {
      return undefined;
    }
    const currentStrategy = strategies.find(
      (s) => s.name === rule.masking_strategy?.strategy,
    );
    return currentStrategy?.description;
  }, [strategies, rule.masking_strategy?.strategy]);

  return (
    <Form layout="vertical" disabled className="max-w-md">
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
        <Form.Item
          extra={currentStrategyDescription}
          label={
            <Flex align="center" gap="small">
              Masking strategy
              {strategies && strategies.length > 0 && (
                <InfoPopover
                  title="Available masking strategies"
                  content={
                    <dl className="max-w-sm px-4 py-3 leading-tight">
                      {strategies.map((s) => (
                        <div key={s.name} className="py-1">
                          <dt className="inline">
                            <Text strong size="sm">
                              {formatMaskingStrategyName(s.name)}
                            </Text>
                          </dt>
                          {": "}
                          <dd className="inline">
                            <Text type="secondary" size="sm">
                              {s.description}
                            </Text>
                          </dd>
                        </div>
                      ))}
                    </dl>
                  }
                />
              )}
            </Flex>
          }
        >
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
            value={rule.storage_destination?.name ?? "No storage destination"}
            disabled
            data-testid={`rule-storage-${rule.key}`}
          />
        </Form.Item>
      )}

      {/* NOTE: targets are not available in the API yet */}
    </Form>
  );
};

export default RulePanel;
