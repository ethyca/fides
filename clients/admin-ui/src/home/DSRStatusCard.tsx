import {
  antTheme,
  Flex,
  Skeleton,
  StackedBarChart,
  Statistic,
  Text,
} from "fidesui";
import NextLink from "next/link";
import { useRouter } from "next/router";
import { useCallback } from "react";

import { PRIVACY_REQUESTS_ROUTE } from "~/features/common/nav/routes";
import { useGetPrivacyRequestsQuery } from "~/features/dashboard/dashboard.slice";

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

  const handleTypeClick = useCallback(
    (type: string) => {
      router.push(
        `${PRIVACY_REQUESTS_ROUTE}?action_type=${type.toLowerCase()}`,
      );
    },
    [router],
  );

  if (isLoading) {
    return <Skeleton active paragraph={{ rows: 6 }} />;
  }

  return (
    <Flex vertical>
      {/* Header */}
      <Flex align="center" justify="space-between" className="mb-5">
        <Text
          type="secondary"
          style={{
            fontFamily: token.fontFamilyCode,
            fontSize: 10,
            fontWeight: 500,
            letterSpacing: "1.5px",
            textTransform: "uppercase",
          }}
        >
          DSR Status
        </Text>
        <NextLink
          href={PRIVACY_REQUESTS_ROUTE}
          style={{
            fontSize: 12,
            fontWeight: 500,
            color: "var(--fidesui-terracotta)",
            textDecoration: "none",
          }}
        >
          View all requests &rarr;
        </NextLink>
      </Flex>

      {/* Hero stat row */}
      <Flex
        align="baseline"
        gap={32}
        className="mb-6 border-b border-solid border-neutral-100 pb-6"
      >
        <Flex align="baseline" gap={10}>
          <Statistic
            value={data?.active_count ?? 0}
            valueStyle={{
              fontSize: 48,
              fontWeight: 200,
              lineHeight: 1,
            }}
          />
          <Text type="secondary" className="text-sm">
            active requests
          </Text>
        </Flex>

        <Flex gap={24} className="flex-1">
          {SUB_STATS.map(({ key, title }) => (
            <div key={key}>
              <Statistic
                value={data?.statuses?.[key] ?? 0}
                valueStyle={{
                  fontSize: 22,
                  fontWeight: 500,
                  lineHeight: 1.2,
                }}
              />
              <Text type="secondary" className="mt-0.5 text-[11px]">
                {title}
              </Text>
            </div>
          ))}
          {(data?.overdue_count ?? 0) > 0 && (
            <NextLink
              href={`${PRIVACY_REQUESTS_ROUTE}?is_overdue=true`}
              style={{ textDecoration: "none" }}
            >
              <Statistic
                value={data?.overdue_count ?? 0}
                valueStyle={{
                  fontSize: 22,
                  fontWeight: 500,
                  lineHeight: 1.2,
                  color: token.colorError,
                }}
              />
              <Text
                type="danger"
                className="mt-0.5 text-[11px]"
              >
                Overdue
              </Text>
            </NextLink>
          )}
        </Flex>
      </Flex>

      {/* SLA Health */}
      <Text
        type="secondary"
        style={{
          fontFamily: token.fontFamilyCode,
          fontSize: 10,
          fontWeight: 500,
          letterSpacing: "1.5px",
          textTransform: "uppercase",
          marginBottom: 8,
        }}
      >
        SLA Health
      </Text>
      {data?.sla_health && (
        <>
          <div className="mb-3">
            <StackedBarChart
              data={data.sla_health}
              segments={SLA_SEGMENTS}
              onCategoryClick={handleTypeClick}
            />
          </div>
          <Flex gap={16}>
            {SLA_SEGMENTS.map(({ color, label }) => (
              <Flex key={label} align="center" gap={5}>
                <div
                  className="size-1.5 rounded-sm"
                  style={{ backgroundColor: token[color] }}
                />
                <Text type="secondary" className="text-[11px]">
                  {label}
                </Text>
              </Flex>
            ))}
          </Flex>
        </>
      )}
    </Flex>
  );
};
