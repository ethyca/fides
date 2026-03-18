import {
  antTheme,
  Card,
  Flex,
  Icons,
  Spin,
  StackedBarChart,
  Statistic,
  Text,
} from "fidesui";
import NextLink from "next/link";
import { useRouter } from "next/router";
import { useCallback } from "react";

import { PRIVACY_REQUESTS_ROUTE } from "~/features/common/nav/routes";
import { useGetPrivacyRequestsQuery } from "~/features/dashboard/dashboard.slice";

import styles from "./DSRStatusCard.module.scss";

const SUB_STATS = [
  { key: "in_progress", title: "In Progress" },
  { key: "pending_action", title: "Pending Action" },
  { key: "awaiting_approval", title: "Awaiting Approval" },
] as const;

const SLA_SEGMENTS = [
  { key: "on_track", color: "colorSuccess", label: "On track" },
  { key: "approaching", color: "colorWarning", label: "Approaching" },
  { key: "overdue", color: "colorError", label: "Overdue" },
] as const;

export const DSRStatusCard = () => {
  const { token } = antTheme.useToken();
  const router = useRouter();
  const { data, isLoading } = useGetPrivacyRequestsQuery();

  const sla = data?.sla_health;

  const handleTypeClick = useCallback(
    (type: string) => {
      router.push(`${PRIVACY_REQUESTS_ROUTE}?action_type=${type}`);
    },
    [router],
  );

  return (
    <Spin spinning={isLoading}>
      <Card
        title="DSR Status"
        extra={
          <NextLink href={PRIVACY_REQUESTS_ROUTE}>
            <Flex align="center" gap={4} className="text-xs">
              View all requests
              <Icons.ArrowRight size={12} />
            </Flex>
          </NextLink>
        }
        variant="borderless"
        className={styles.cardContainer}
      >
        <Flex vertical gap="middle">
          <Flex>
            <Flex
              vertical
              justify="space-between"
              className="w-[180px] shrink-0 border-r border-solid border-r-[var(--ant-color-border)] pr-5"
            >
              <div>
                <Flex align="baseline" gap="middle">
                  <Statistic value={data?.active_count ?? 0} />
                  <Text type="secondary" className="text-xs">
                    Active Requests
                  </Text>
                </Flex>
                <Flex vertical gap={4} className="mt-3">
                  {SUB_STATS.map(({ key, title }) => (
                    <Flex key={key} className={styles.subStat}>
                      <Statistic
                        value={data?.statuses[key] ?? 0}
                        title={title}
                        valueStyle={{
                          fontSize: token.fontSize,
                          fontWeight: 600,
                        }}
                      />
                    </Flex>
                  ))}
                </Flex>
              </div>
              {(data?.overdue_count ?? 0) > 0 && (
                <NextLink
                  href={PRIVACY_REQUESTS_ROUTE}
                  className={styles.overdueLink}
                >
                  <Flex align="center" gap={4}>
                    <Text type="danger" className="text-xs font-semibold">
                      {data?.overdue_count} overdue
                    </Text>
                    <Icons.ArrowRight size={12} />
                  </Flex>
                </NextLink>
              )}
            </Flex>

            <Flex vertical className="min-w-0 flex-1 pl-5">
              <Text strong className="mb-3 text-xs">
                SLA Health
              </Text>
              <div className="flex-1">
                {sla && (
                  <StackedBarChart
                    data={sla}
                    segments={SLA_SEGMENTS}
                    onCategoryClick={handleTypeClick}
                  />
                )}
              </div>
              <Flex gap={10} className="mt-2">
                {SLA_SEGMENTS.map(({ color, label }) => (
                  <Flex key={label} align="center" gap={4}>
                    <div
                      className="size-2 rounded-sm"
                      style={{ backgroundColor: token[color] }}
                    />
                    <Text type="secondary" className="text-[10px]">
                      {label}
                    </Text>
                  </Flex>
                ))}
              </Flex>
            </Flex>
          </Flex>
        </Flex>
      </Card>
    </Spin>
  );
};
