import dayjs from "dayjs";
import {
  Button,
  Card,
  CheckOutlined,
  CUSTOM_TAG_COLOR,
  Flex,
  List,
  Tag,
  Text,
} from "fidesui";
import NextLink from "next/link";
import { useCallback, useMemo, useState } from "react";

import { capitalize } from "~/features/common/utils";
import {
  ACTION_CTA,
  DIMENSION_LABELS,
  getUrgencyGroup,
  URGENCY_TABS,
} from "~/features/dashboard/constants";
import { useGetPriorityActionsQuery } from "~/features/dashboard/dashboard.slice";
import type { PriorityAction } from "~/features/dashboard/types";
import { ActionSeverity } from "~/features/dashboard/types";

import styles from "./PriorityActionsCard.module.scss";
import { clearDimensionFilter, useDimensionFilter } from "./useDimensionFilter";

const SEVERITY_TAG_COLOR: Record<string, CUSTOM_TAG_COLOR> = {
  [ActionSeverity.CRITICAL]: CUSTOM_TAG_COLOR.ERROR,
  [ActionSeverity.HIGH]: CUSTOM_TAG_COLOR.WARNING,
  [ActionSeverity.MEDIUM]: CUSTOM_TAG_COLOR.DEFAULT,
  [ActionSeverity.LOW]: CUSTOM_TAG_COLOR.DEFAULT,
};

function getDaysRemaining(dueDate: string | null): {
  label: string;
  color: CUSTOM_TAG_COLOR;
} | null {
  if (!dueDate) {
    return null;
  }
  const days = dayjs(dueDate).diff(dayjs(), "day");
  if (days < 0) {
    return {
      label: `${Math.abs(days)}d overdue`,
      color: CUSTOM_TAG_COLOR.ERROR,
    };
  }
  if (days <= 3) {
    return { label: `${days}d left`, color: CUSTOM_TAG_COLOR.WARNING };
  }
  return { label: `${days}d left`, color: CUSTOM_TAG_COLOR.DEFAULT };
}

const MAX_VISIBLE_ITEMS = 4;

export const PriorityActionsCard = () => {
  const dimensionFilter = useDimensionFilter();
  const { data, isLoading } = useGetPriorityActionsQuery(
    dimensionFilter ? { dimension: dimensionFilter } : undefined,
  );
  const [activeTab, setActiveTab] = useState("overdue");
  const [showAll, setShowAll] = useState(false);

  const toggleShowAll = useCallback(() => setShowAll((prev) => !prev), []);

  const countsByGroup = useMemo(() => {
    const counts: Record<string, number> = {
      overdue: 0,
      urgent: 0,
      pending: 0,
    };
    data?.items?.forEach((action) => {
      const group = getUrgencyGroup(action.severity, action.due_date);
      counts[group] = (counts[group] ?? 0) + 1;
    });
    return counts;
  }, [data]);

  const allFilteredActions = useMemo(() => {
    if (!data?.items) {
      return [];
    }
    return data.items.filter(
      (action) =>
        getUrgencyGroup(action.severity, action.due_date) === activeTab,
    );
  }, [data, activeTab]);

  const filteredActions =
    showAll || allFilteredActions.length <= MAX_VISIBLE_ITEMS
      ? allFilteredActions
      : allFilteredActions.slice(0, MAX_VISIBLE_ITEMS);
  const hasMore = allFilteredActions.length > MAX_VISIBLE_ITEMS;

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
          const daysInfo = getDaysRemaining(action.due_date);
          return (
            <List.Item
              key={action.id}
              actions={[
                <NextLink
                  key="cta"
                  href={cta.route(action.action_data)}
                  passHref
                >
                  <Button size="small">{cta.label}</Button>
                </NextLink>,
              ]}
            >
              <List.Item.Meta
                title={
                  <Flex gap={6} align="center">
                    {action.title}
                    <Tag color={SEVERITY_TAG_COLOR[action.severity]}>
                      {capitalize(action.severity)}
                    </Tag>
                    {daysInfo && (
                      <Tag color={daysInfo.color}>{daysInfo.label}</Tag>
                    )}
                  </Flex>
                }
                description={
                  <Text type="secondary" ellipsis={{ tooltip: true }}>
                    {action.message}
                  </Text>
                }
              />
            </List.Item>
          );
        }}
      />
      {hasMore && (
        <Flex justify="center" className="mt-2">
          <Button type="link" size="small" onClick={toggleShowAll}>
            {showAll
              ? "Show less"
              : `View all ${allFilteredActions.length} actions`}
          </Button>
        </Flex>
      )}
    </Card>
  );
};
