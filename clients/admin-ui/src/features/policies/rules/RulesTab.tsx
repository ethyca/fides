import { Collapse, CollapseProps, Empty, Flex, Tag, Typography } from "fidesui";
import { useMemo } from "react";

import RulePanel from "~/features/policies/rules/RulePanel";
import { RuleResponse } from "~/types/api";

const { Paragraph, Text } = Typography;

interface RulesTabProps {
  rules: RuleResponse[];
}

const RulesTab = ({ rules = [] }: RulesTabProps) => {
  const collapseItems: CollapseProps["items"] = useMemo(
    () =>
      rules?.map((rule: RuleResponse) => ({
        key: rule.key ?? rule.name,
        label: (
          <Flex align="center" gap="small">
            <Text strong>{rule.name}</Text>
            <Tag className="capitalize">{rule.action_type}</Tag>
          </Flex>
        ),
        children: <RulePanel rule={rule} />,
      })),
    [rules],
  );

  if (!rules || rules.length === 0) {
    return <Empty description="No rules configured for this policy" />;
  }

  return (
    <Flex vertical gap="large">
      <Flex vertical gap="small">
        <Typography.Title level={5}>Policy rules</Typography.Title>
        <Paragraph type="secondary" className="max-w-screen-md">
          Rules define what actions to take on data that matches specific data
          categories. Each rule specifies an action type (access, erasure,
          etc.), target data categories, and optionally a masking strategy or
          storage destination.
        </Paragraph>
      </Flex>

      {rules.length === 0 ? (
        <Empty
          description="No rules configured for this policy"
          className="py-8"
        />
      ) : (
        <Collapse
          items={collapseItems}
          defaultActiveKey={
            rules.length > 1 ? undefined : rules.map((r) => r.key ?? r.name) // Default to open if there is only one rule
          }
          data-testid="rules-collapse"
        />
      )}
    </Flex>
  );
};

export default RulesTab;
