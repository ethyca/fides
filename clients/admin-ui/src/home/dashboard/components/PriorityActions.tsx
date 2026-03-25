import { Card, Flex, Tabs, Tag, Typography } from "fidesui";
import { theme } from "antd/lib";

import type { ActionTab } from "../types";

const { Text } = Typography;

const DEFAULT_TAG_COLOR = "default";

interface PriorityActionsProps {
  tabs: ActionTab[];
}

const PriorityActions = ({ tabs }: PriorityActionsProps) => {
  const { token } = theme.useToken();

  const items = tabs.map((tab) => ({
    key: tab.key,
    label: (
      <span className="text-[11px]">
        {tab.label}{" "}
        <Text type="secondary" className="text-[10px]">
          {tab.count}
        </Text>
      </span>
    ),
    children: (
      <Flex vertical gap={0}>
        {tab.items.map((item) => (
          <Flex
            key={item.id}
            align="center"
            justify="space-between"
            gap={8}
            className="py-[8px]"
            style={{ borderBottom: `1px solid ${token.colorBorder}` }}
          >
            {/* Left: title (header) + subject + status tag + request type */}
            <Flex align="center" gap={8} className="min-w-0 flex-1">
              <Text strong className="text-[12px] whitespace-nowrap">
                {item.title}
              </Text>
              {item.subject && (
                <Text type="secondary" className="text-[11px] whitespace-nowrap">
                  {item.subject}
                </Text>
              )}
              {item.status && (
                <Tag
                  className="shrink-0"
                  bordered={false}
                  style={{
                    backgroundColor: token.colorFillSecondary,
                    color: token.colorText,
                  }}
                >
                  {item.status}
                </Tag>
              )}
              {item.requestType && (
                <Text type="secondary" className="text-[11px] whitespace-nowrap">
                  {item.requestType}
                </Text>
              )}
            </Flex>

            {/* Right: SLA + date + view link */}
            <Flex align="center" gap={10} className="shrink-0">
              {item.daysRemaining != null && (
                <Text
                  className="text-[10px] font-semibold whitespace-nowrap"
                  style={{
                    color:
                      item.daysRemaining <= 0
                        ? token.colorError
                        : item.daysRemaining <= 2
                          ? token.colorWarning
                          : token.colorSuccess,
                  }}
                >
                  {item.daysRemaining <= 0
                    ? `${Math.abs(item.daysRemaining)}d overdue`
                    : `${item.daysRemaining}d left`}
                </Text>
              )}
              {item.submitted && (
                <Text type="secondary" className="text-[10px] whitespace-nowrap">
                  {item.submitted}
                </Text>
              )}
              <Text
                type="secondary"
                className="text-[10px] whitespace-nowrap cursor-pointer"
              >
                View →
              </Text>
            </Flex>
          </Flex>
        ))}
      </Flex>
    ),
  }));

  return (
    <Card className="rounded-lg h-full" styles={{ body: { padding: "14px 20px" } }}>
      <Flex align="center" justify="space-between" className="mb-1">
        <Text
          className="text-[10px] tracking-[0.1em]"
          type="secondary"
          strong
        >
          PRIORITY ACTIONS
        </Text>
      </Flex>
      <Tabs
        items={items}
        size="small"
        tabBarStyle={{ marginBottom: 4 }}
        tabBarGutter={16}
      />
    </Card>
  );
};

export default PriorityActions;
