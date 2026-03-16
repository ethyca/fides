import {
  Avatar,
  Button,
  Card,
  CheckOutlined,
  Flex,
  Icons,
  List,
  Tag,
  Text,
} from "fidesui";
import { useRouter } from "next/router";
import { type ReactNode, useMemo, useState } from "react";

import type { PriorityAction } from "~/features/dashboard/dashboard.slice";
import { useGetPriorityActionsQuery } from "~/features/dashboard/dashboard.slice";

import { DIMENSION_LABELS } from "./posture-constants";
import styles from "./PriorityActionsCard.module.scss";
import { clearDimensionFilter, useDimensionFilter } from "./useDimensionFilter";

type UrgencyGroup = "act_now" | "this_week" | "when_ready";

const ACTION_TYPE_ICON: Record<PriorityAction["type"], ReactNode> = {
  classification_review: <Icons.Tag size={16} />,
  dsr_action: <Icons.Time size={16} />,
  system_review: <Icons.DataBase size={16} />,
  steward_assignment: <Icons.UserAvatar size={16} />,
  consent_anomaly: <Icons.WarningAlt size={16} />,
  policy_violation: <Icons.Policy size={16} />,
  pia_update: <Icons.Document size={16} />,
};

const ACTION_CTA: Record<
  PriorityAction["type"],
  { label: string; route: (data: Record<string, unknown>) => string }
> = {
  classification_review: {
    label: "Review classifications",
    route: () => "/data-discovery/action-center",
  },
  dsr_action: {
    label: "View request",
    route: (d) => `/privacy-requests/${d.request_id}`,
  },
  system_review: {
    label: "Review system",
    route: () => "/data-discovery/action-center",
  },
  steward_assignment: {
    label: "Assign steward",
    route: (d) =>
      d.system_id ? `/systems/configure/${d.system_id}` : "/systems",
  },
  consent_anomaly: {
    label: "Investigate",
    route: () => "/consent/reporting",
  },
  policy_violation: {
    label: "Review violation",
    route: (d) => `/systems/configure/${d.system_id}`,
  },
  pia_update: {
    label: "View assessment",
    route: (d) => `/systems/configure/${d.system_id}`,
  },
};

function getUrgencyGroup(action: PriorityAction): UrgencyGroup {
  if (action.severity === "critical" || action.severity === "high") {
    return "act_now";
  }
  if (action.due_date) {
    return "this_week";
  }
  return "when_ready";
}

const TABS = [
  { key: "act_now", label: "Act Now" },
  { key: "this_week", label: "This Week" },
  { key: "when_ready", label: "When Ready" },
];

export const PriorityActionsCard = () => {
  const router = useRouter();
  const dimensionFilter = useDimensionFilter();
  const { data, isLoading } = useGetPriorityActionsQuery(
    dimensionFilter ? { dimension: dimensionFilter } : undefined,
  );
  const [activeTab, setActiveTab] = useState("act_now");

  const countsByGroup = useMemo(() => {
    const counts: Record<string, number> = {
      act_now: 0,
      this_week: 0,
      when_ready: 0,
    };
    data?.items?.forEach((action) => {
      const group = getUrgencyGroup(action);
      counts[group] = (counts[group] ?? 0) + 1;
    });
    return counts;
  }, [data]);

  const filteredActions = useMemo(() => {
    if (!data?.items) {
      return [];
    }
    return data.items.filter((action) => getUrgencyGroup(action) === activeTab);
  }, [data, activeTab]);

  return (
    <Card
      title="Priority actions"
      variant="borderless"
      className={styles.cardContainer}
      headerLayout="inline"
      tabList={TABS.map((tab) => ({
        key: tab.key,
        label: (
          <span>
            {tab.label} <Tag color="default">{countsByGroup[tab.key]}</Tag>
          </span>
        ),
      }))}
      activeTabKey={activeTab}
      onTabChange={setActiveTab}
    >
      {dimensionFilter && (
        <Flex className="mb-2">
          <Tag closable onClose={clearDimensionFilter} color="minos">
            Filtered: {DIMENSION_LABELS[dimensionFilter] ?? dimensionFilter}
          </Tag>
        </Flex>
      )}
      <List
        dataSource={filteredActions}
        loading={isLoading}
        locale={{
          emptyText: (
            <Flex
              vertical
              align="center"
              justify="center"
              gap={8}
              className={styles.emptyActions}
            >
              <CheckOutlined className={styles.emptyIcon} />
              <Text type="secondary">
                All clear. Your governance posture is strong.
              </Text>
            </Flex>
          ),
        }}
        size="small"
        renderItem={(action) => {
          const cta = ACTION_CTA[action.type];
          return (
            <List.Item
              key={action.id}
              actions={[
                <Button
                  key="cta"
                  size="small"
                  className="mt-1"
                  onClick={() => router.push(cta.route(action.action_data))}
                >
                  {cta.label}
                </Button>,
              ]}
            >
              <List.Item.Meta
                avatar={
                  <Avatar
                    size={32}
                    icon={ACTION_TYPE_ICON[action.type]}
                    className={styles.actionIcon}
                  />
                }
                title={action.title}
                description={action.message}
              />
            </List.Item>
          );
        }}
      />
    </Card>
  );
};
