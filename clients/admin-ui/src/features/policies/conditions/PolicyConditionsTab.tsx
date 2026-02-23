import { Flex, List, Tag, Tooltip, Typography } from "fidesui";
import { useMemo } from "react";

import { operatorLabels } from "~/features/integrations/configure-tasks/constants";
import {
  formatConditionValue,
  formatFieldDisplay,
} from "~/features/integrations/configure-tasks/utils";
import { extractLeafConditions } from "~/features/policies/utils/extractLeafConditions";
import type { ConditionGroup, ConditionLeaf } from "~/types/api";

const { Title, Paragraph, Text } = Typography;

interface PolicyConditionsTabProps {
  conditions?: ConditionGroup | ConditionLeaf | null;
}

export const PolicyConditionsTab = ({
  conditions,
}: PolicyConditionsTabProps) => {
  const leafConditions = useMemo(
    () => extractLeafConditions(conditions),
    [conditions],
  );

  return (
    <div>
      <Title level={5} data-testid="policy-conditions-title">
        Policy conditions
      </Title>
      <Paragraph
        type="secondary"
        className="w-2/3"
        data-testid="policy-conditions-description"
      >
        Configure conditions that control when this policy applies to privacy
        requests. If no conditions are set, the policy will apply to all
        matching requests.
      </Paragraph>
      <Paragraph strong data-testid="policy-conditions-note">
        All conditions must be met for the policy to apply.
      </Paragraph>

      <List
        dataSource={leafConditions}
        data-testid="conditions-list"
        locale={{
          emptyText: (
            <div className="py-8 text-center">
              <Text type="secondary">
                No conditions configured. This policy will apply to all matching
                requests.
              </Text>
            </div>
          ),
        }}
        renderItem={(condition: ConditionLeaf, index: number) => {
          const formattedValue = formatConditionValue(condition);
          return (
            <List.Item key={index} data-testid={`condition-row-${index}`}>
              <List.Item.Meta
                title={
                  <Flex gap={8} align="center" className="font-normal">
                    <div className="max-w-[300px]">
                      <Tooltip title={condition.field_address}>
                        <Text>
                          {formatFieldDisplay(condition.field_address)}
                        </Text>
                      </Tooltip>
                    </div>
                    <Tag color="sandstone">
                      {operatorLabels[condition.operator]}
                    </Tag>
                    {formattedValue && (
                      <div className="max-w-[300px]">
                        <Text ellipsis={{ tooltip: formattedValue }}>
                          {formattedValue}
                        </Text>
                      </div>
                    )}
                  </Flex>
                }
              />
            </List.Item>
          );
        }}
      />
    </div>
  );
};
