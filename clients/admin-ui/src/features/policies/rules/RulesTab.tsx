import {
  Collapse,
  CollapseProps,
  Empty,
  Flex,
  Tag,
  Typography,
} from "fidesui";
import { useMemo } from "react";

import { useGetPolicyRulesQuery } from "~/features/policy/policy.slice";
import RulePanel from "~/features/policies/rules/RulePanel";
import { ActionType, RuleResponseWithTargets } from "~/types/api";

const { Paragraph, Text } = Typography;

const actionTypeColors: Record<ActionType, string> = {
  [ActionType.ACCESS]: "success",
  [ActionType.ERASURE]: "error",
  [ActionType.CONSENT]: "corinth",
  [ActionType.UPDATE]: "warning",
};

interface RulesTabProps {
  policyKey: string;
}

const RulesTab = ({ policyKey }: RulesTabProps) => {
  const {
    data: rulesData,
    isLoading,
    error,
  } = useGetPolicyRulesQuery(policyKey, {
    skip: !policyKey,
  });

  const rules = useMemo(() => rulesData?.items ?? [], [rulesData]);

  const collapseItems: CollapseProps["items"] = useMemo(
    () =>
      rules.map((rule: RuleResponseWithTargets) => ({
        key: rule.key ?? rule.name,
        label: (
          <Flex align="center" gap={8}>
            <Text strong>{rule.name}</Text>
            <Tag color={actionTypeColors[rule.action_type]} className="capitalize">
              {rule.action_type}
            </Tag>
          </Flex>
        ),
        children: <RulePanel rule={rule} />,
      })),
    [rules]
  );

  if (isLoading) {
    return (
      <div className="py-4">
        <Text type="secondary">Loading rules...</Text>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-4">
        <Text type="danger">
          Failed to load rules. Please refresh the page and try again.
        </Text>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-4">
        <Typography.Title level={5}>Policy rules</Typography.Title>
        <Paragraph type="secondary">
          Rules define what actions to take on data that matches specific data
          categories. Each rule specifies an action type (access, erasure, etc.),
          target data categories, and optionally a masking strategy or storage
          destination.
        </Paragraph>
      </div>

      {rules.length === 0 ? (
        <Empty
          description="No rules configured for this policy"
          className="py-8"
        />
      ) : (
        <Collapse
          items={collapseItems}
          defaultActiveKey={rules.map((r) => r.key ?? r.name)}
          data-testid="rules-collapse"
        />
      )}
    </div>
  );
};

export default RulesTab;
