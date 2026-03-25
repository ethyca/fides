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
import NextLink from "next/link";
import { type ReactNode, useMemo, useState } from "react";

import {
  ACTION_CTA,
  DIMENSION_LABELS,
  getUrgencyGroup,
  URGENCY_TABS,
} from "~/features/dashboard/constants";
import { useGetPriorityActionsQuery } from "~/features/dashboard/dashboard.slice";
import type { PriorityAction } from "~/features/dashboard/types";
import { ActionType } from "~/features/dashboard/types";

import styles from "./PriorityActionsCard.module.scss";
import { clearDimensionFilter, useDimensionFilter } from "./useDimensionFilter";

const ACTION_TYPE_ICON: Record<ActionType, ReactNode> = {
  [ActionType.CLASSIFICATION_REVIEW]: <Icons.Tag size={16} />,
  [ActionType.DSR_ACTION]: <Icons.Time size={16} />,
  [ActionType.SYSTEM_REVIEW]: <Icons.DataBase size={16} />,
  [ActionType.STEWARD_ASSIGNMENT]: <Icons.UserAvatar size={16} />,
  [ActionType.CONSENT_ANOMALY]: <Icons.WarningAlt size={16} />,
  [ActionType.POLICY_VIOLATION]: <Icons.Policy size={16} />,
  [ActionType.PIA_UPDATE]: <Icons.Document size={16} />,
};

export const PriorityActionsCard = () => {
  const dimensionFilter = useDimensionFilter();
  const { data, isLoading } = useGetPriorityActionsQuery(
    dimensionFilter ? { dimension: dimensionFilter } : undefined,
  );
  const [activeTab, setActiveTab] = useState("act_now");

  const countsByGroup = useMemo(() => {
    const counts: Record<string, number> = {
      act_now: 0,
      scheduled: 0,
      when_ready: 0,
    };
    data?.items?.forEach((action) => {
      const group = getUrgencyGroup(action.severity, action.due_date);
      counts[group] = (counts[group] ?? 0) + 1;
    });
    return counts;
  }, [data]);

  const filteredActions = useMemo(() => {
    if (!data?.items) {
      return [];
    }
    return data.items.filter(
      (action) =>
        getUrgencyGroup(action.severity, action.due_date) === activeTab,
    );
  }, [data, activeTab]);

  return (
    <Card
      title="Priority actions"
      variant="borderless"
      className={styles.cardContainer}
      tabList={URGENCY_TABS.map((tab) => ({
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
        renderItem={(action: PriorityAction) => {
          const cta = ACTION_CTA[action.type];
          return (
            <List.Item
              key={action.id}
              actions={[
                <NextLink
                  key="cta"
                  href={cta.route(action.action_data)}
                  passHref
                >
                  <Button size="small" className="mt-1">
                    {cta.label}
                  </Button>
                </NextLink>,
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
