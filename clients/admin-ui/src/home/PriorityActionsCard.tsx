import dayjs from "dayjs";
import {
  Card,
  CheckOutlined,
  CUSTOM_TAG_COLOR,
  Flex,
  Icons,
  List,
  Select,
  Tag,
  Text,
} from "fidesui";
import { useMemo, useState } from "react";

import { RouterLink } from "~/features/common/nav/RouterLink";
import { capitalize } from "~/features/common/utils";
import {
  ACTION_CTA,
  DIMENSION_LABELS,
  getUrgencyGroup,
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

const STATUS_FILTER_OPTIONS = [
  { value: "all", label: "Any" },
  { value: "overdue", label: "Overdue" },
  { value: "urgent", label: "Requires Attention" },
  { value: "pending", label: "Pending" },
];

const SEVERITY_FILTER_OPTIONS = [
  { value: "all", label: "Any" },
  { value: ActionSeverity.CRITICAL, label: "Critical" },
  { value: ActionSeverity.HIGH, label: "High" },
  { value: ActionSeverity.MEDIUM, label: "Medium" },
  { value: ActionSeverity.LOW, label: "Low" },
];

export const PriorityActionsCard = () => {
  const dimensionFilter = useDimensionFilter();
  const { data, isLoading } = useGetPriorityActionsQuery(
    dimensionFilter ? { dimension: dimensionFilter } : undefined,
  );
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [severityFilter, setSeverityFilter] = useState<string>("all");

  const filteredActions = useMemo(() => {
    if (!data?.items) {
      return [];
    }
    return data.items.filter((action) => {
      if (severityFilter !== "all" && action.severity !== severityFilter) {
        return false;
      }
      if (statusFilter !== "all") {
        const group = getUrgencyGroup(action.severity, action.due_date);
        if (group !== statusFilter) {
          return false;
        }
      }
      return true;
    });
  }, [data, severityFilter, statusFilter]);

  return (
    <Card
      title="Priority actions"
      variant="borderless"
      className={styles.cardContainer}
      extra={
        <Flex gap={12} align="center">
          <Flex align="center" gap={4}>
            <Text type="secondary" className="text-xs">
              Status
            </Text>
            <Select
              size="small"
              showSearch={false}
              value={statusFilter}
              onChange={setStatusFilter}
              options={STATUS_FILTER_OPTIONS}
              style={{ width: 130, cursor: "pointer" }}
              className={styles.filterSelect}
              aria-label="Status"
            />
          </Flex>
          <Flex align="center" gap={4}>
            <Text type="secondary" className="text-xs">
              Severity
            </Text>
            <Select
              size="small"
              showSearch={false}
              value={severityFilter}
              onChange={setSeverityFilter}
              options={SEVERITY_FILTER_OPTIONS}
              style={{ width: 110, cursor: "pointer" }}
              className={styles.filterSelect}
              aria-label="Severity"
            />
          </Flex>
        </Flex>
      }
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
          const href = cta.route(action.action_data);
          const daysInfo = getDaysRemaining(action.due_date);
          return (
            <RouterLink
              unstyled
              key={action.id}
              href={href}
              className={styles.actionRow}
            >
              <List.Item>
                <List.Item.Meta
                  title={
                    <Flex gap={6} align="center" wrap={false}>
                      <Text ellipsis={{ tooltip: true }}>{action.title}</Text>
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
                <Icons.Launch size={14} className={styles.launchIcon} />
              </List.Item>
            </RouterLink>
          );
        }}
      />
    </Card>
  );
};
