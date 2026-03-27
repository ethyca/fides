import dayjs from "dayjs";
import {
  antTheme,
  Button,
  CheckOutlined,
  CUSTOM_TAG_COLOR,
  Flex,
  List,
  Tabs,
  TabsProps,
  Tag,
  Text,
} from "fidesui";
import NextLink from "next/link";
import { useMemo, useState } from "react";

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

const MAX_VISIBLE_ACTIONS = 5;

const DUE_COLORS: Record<string, string | undefined> = {
  overdue: "var(--fidesui-error)",
  approaching: "var(--fidesui-warning)",
};

function getDaysRemaining(dueDate: string | null): {
  label: string;
  color: CUSTOM_TAG_COLOR;
  urgency: string;
} | null {
  if (!dueDate) {
    return null;
  }
  const days = dayjs(dueDate).diff(dayjs(), "day");
  if (days < 0) {
    return {
      label: `${Math.abs(days)}d overdue`,
      color: CUSTOM_TAG_COLOR.ERROR,
      urgency: "overdue",
    };
  }
  if (days <= 3) {
    return { label: `${days}d left`, color: CUSTOM_TAG_COLOR.WARNING, urgency: "approaching" };
  }
  return { label: `${days}d left`, color: CUSTOM_TAG_COLOR.DEFAULT, urgency: "ok" };
}

export const PriorityActionsCard = () => {
  const { token } = antTheme.useToken();
  const dimensionFilter = useDimensionFilter();
  const { data, isLoading } = useGetPriorityActionsQuery(
    dimensionFilter ? { dimension: dimensionFilter } : undefined,
  );
  const [activeTab, setActiveTab] = useState("act_now");
  const [expanded, setExpanded] = useState(false);

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

  const totalCount = useMemo(
    () => Object.values(countsByGroup).reduce((a, b) => a + b, 0),
    [countsByGroup],
  );

  const filteredActions = useMemo(() => {
    if (!data?.items) {
      return [];
    }
    return data.items.filter(
      (action) =>
        getUrgencyGroup(action.severity, action.due_date) === activeTab,
    );
  }, [data, activeTab]);

  const visibleActions = expanded
    ? filteredActions
    : filteredActions.slice(0, MAX_VISIBLE_ACTIONS);
  const hiddenCount = filteredActions.length - visibleActions.length;

  return (
    <Flex vertical>
      {/* Header: section label + tabs */}
      <Text
        type="secondary"
        className={styles.sectionLabel}
        style={{ fontFamily: token.fontFamilyCode }}
      >
        Priority Actions
      </Text>
      <Tabs
        activeKey={activeTab}
        onChange={(key: string) => {
          setActiveTab(key);
          setExpanded(false);
        }}
        items={URGENCY_TABS.map((tab) => ({
          key: tab.key,
          label: (
            <span>
              {tab.label}{" "}
              <Tag color="default" className="!ml-1">
                {countsByGroup[tab.key]}
              </Tag>
            </span>
          ),
        }))}
      />

      {dimensionFilter && (
        <Flex className="mb-2">
          <Tag closable onClose={clearDimensionFilter} color="minos">
            Filtered: {DIMENSION_LABELS[dimensionFilter] ?? dimensionFilter}
          </Tag>
        </Flex>
      )}

      {/* Action list — no Card wrapper */}
      <List
        dataSource={visibleActions}
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
              className={styles.actionItem}
              actions={[
                ...(daysInfo
                  ? [
                      <Text
                        key="due"
                        className={styles.dueText}
                        style={{
                          fontFamily: token.fontFamilyCode,
                          color: DUE_COLORS[daysInfo.urgency] ?? token.colorTextDisabled,
                          fontWeight: daysInfo.urgency === "overdue" ? 600 : 500,
                        }}
                      >
                        {daysInfo.label}
                      </Text>,
                    ]
                  : []),
                <NextLink
                  key="cta"
                  href={cta.route(action.action_data)}
                  className={styles.ctaLink}
                >
                  {cta.label} &rarr;
                </NextLink>,
              ]}
            >
              <List.Item.Meta
                title={action.title}
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

      {/* Expand button */}
      {!expanded && hiddenCount > 0 && (
        <Flex justify="center" className="mt-4">
          <Button onClick={() => setExpanded(true)}>
            Show all actions
            <Tag color="default" className="!ml-2">
              {totalCount}
            </Tag>
          </Button>
        </Flex>
      )}
    </Flex>
  );
};
