import type { AntColorTokenKey } from "fidesui";
import {
  antTheme,
  Badge,
  Card,
  DonutChart,
  Flex,
  Icons,
  Text,
  Tooltip,
} from "fidesui";
import { useMemo } from "react";

import { RouterLink } from "~/features/common/nav/RouterLink";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import {
  AssessmentStatus,
  RiskLevel,
  useGetPrivacyAssessmentsQuery,
} from "~/features/privacy-assessments";
import type {
  AssessmentGroupResponse,
  PrivacyAssessmentResponse,
} from "~/features/privacy-assessments/types";

import styles from "./AssessmentStatusCard.module.scss";

const STALE_DAYS = 14;
const TOP_BLOCKED_LIMIT = 3;

type RiskBucket = RiskLevel | "unrated";

const RISK_BREAKDOWN: {
  key: RiskBucket;
  label: string;
  color: AntColorTokenKey;
}[] = [
  { key: RiskLevel.HIGH, label: "High", color: "colorError" },
  { key: RiskLevel.MEDIUM, label: "Medium", color: "colorWarning" },
  { key: RiskLevel.LOW, label: "Low", color: "colorSuccess" },
  { key: "unrated", label: "Unrated", color: "colorTextQuaternary" },
];

interface BlockedGroup {
  name: string;
  staleCount: number;
  highRiskCount: number;
  totalCount: number;
}

interface AssessmentMetrics {
  total: number;
  byRisk: Record<RiskBucket, number>;
  staleCount: number;
  topBlocked: BlockedGroup[];
}

const EMPTY_RISK_COUNTS: Record<RiskBucket, number> = {
  [RiskLevel.HIGH]: 0,
  [RiskLevel.MEDIUM]: 0,
  [RiskLevel.LOW]: 0,
  unrated: 0,
};

function isStale(
  assessment: PrivacyAssessmentResponse,
  staleBefore: number,
): boolean {
  if (assessment.status === AssessmentStatus.COMPLETED) {
    return false;
  }
  if (!assessment.updated_at) {
    return true;
  }
  const updatedAt = new Date(assessment.updated_at).getTime();
  return Number.isFinite(updatedAt) && updatedAt < staleBefore;
}

function computeMetrics(
  groups: AssessmentGroupResponse[] | undefined,
): AssessmentMetrics {
  const byRisk = { ...EMPTY_RISK_COUNTS };
  const groupAgg = new Map<string, BlockedGroup>();
  let total = 0;
  let staleCount = 0;

  const staleBefore = Date.now() - STALE_DAYS * 24 * 60 * 60 * 1000;

  groups?.forEach((group) => {
    const groupLabel = group.data_use_name ?? "Uncategorized";
    let agg = groupAgg.get(groupLabel);
    if (!agg) {
      agg = {
        name: groupLabel,
        staleCount: 0,
        highRiskCount: 0,
        totalCount: 0,
      };
      groupAgg.set(groupLabel, agg);
    }

    group.assessments?.forEach((assessment) => {
      total += 1;
      agg!.totalCount += 1;
      const riskKey: RiskBucket = assessment.risk_level ?? "unrated";
      byRisk[riskKey] = (byRisk[riskKey] ?? 0) + 1;
      if (assessment.risk_level === RiskLevel.HIGH) {
        agg!.highRiskCount += 1;
      }
      if (isStale(assessment, staleBefore)) {
        staleCount += 1;
        agg!.staleCount += 1;
      }
    });
  });

  const topBlocked = Array.from(groupAgg.values())
    .filter((g) => g.staleCount > 0 || g.highRiskCount > 0)
    .sort(
      (a, b) =>
        b.staleCount + b.highRiskCount - (a.staleCount + a.highRiskCount),
    )
    .slice(0, TOP_BLOCKED_LIMIT);

  return {
    total,
    byRisk,
    staleCount,
    topBlocked,
  };
}

export const AssessmentStatusCard = () => {
  const { token } = antTheme.useToken();
  const { data, isLoading } = useGetPrivacyAssessmentsQuery();

  const metrics = useMemo(() => computeMetrics(data?.items), [data?.items]);

  const riskSegments = RISK_BREAKDOWN.map(({ key, label, color }) => ({
    value: metrics.byRisk[key],
    color,
    name: label,
  }));

  return (
    <Card
      title={
        <Tooltip
          placement="bottom"
          title="A snapshot of your privacy assessments program — open work, risk profile, coverage, and where progress is stalled."
        >
          <Flex
            style={{ cursor: "pointer", display: "inline-flex" }}
            align="center"
            gap={4}
          >
            <Text>Assessment Status</Text>
            <Icons.Help size={14} className="opacity-30" />
          </Flex>
        </Tooltip>
      }
      loading={isLoading}
      extra={
        <RouterLink
          unstyled
          href={PRIVACY_ASSESSMENTS_ROUTE}
          className={styles.viewAllLink}
        >
          <Flex align="center" gap={4}>
            View all
            <Icons.ArrowRight size={14} />
          </Flex>
        </RouterLink>
      }
      variant="borderless"
      className={styles.cardContainer}
    >
      <Flex gap="large" align="stretch">
        <Flex
          vertical
          gap="middle"
          className="w-[240px] shrink-0 border-r border-solid border-r-[var(--ant-color-border)] pr-6"
        >
          <div className="size-[120px] self-center">
            <DonutChart
              variant="thick"
              segments={riskSegments}
              centerLabel={
                <Flex vertical align="center" gap={0}>
                  <Text strong className="text-lg leading-none">
                    {metrics.total}
                  </Text>
                  <Text type="secondary" className="text-[10px]">
                    total
                  </Text>
                </Flex>
              }
            />
          </div>
          <Flex vertical gap={4}>
            {RISK_BREAKDOWN.map(({ key, label, color }) => (
              <Flex key={key} align="center" gap={8}>
                <div
                  className="size-2.5 shrink-0 rounded-full"
                  style={{ backgroundColor: token[color] }}
                />
                <Text strong className="text-sm">
                  {metrics.byRisk[key]}
                </Text>
                <Text type="secondary" className="text-sm">
                  {label}
                </Text>
              </Flex>
            ))}
          </Flex>
        </Flex>

        <Flex vertical gap="middle" className="min-w-0 flex-1">
          {metrics.staleCount > 0 && (
            <RouterLink
              unstyled
              href={`${PRIVACY_ASSESSMENTS_ROUTE}?status=${AssessmentStatus.IN_PROGRESS}`}
              className={styles.staleBadge}
            >
              <Badge
                count={metrics.staleCount}
                color={token.colorWarning}
                size="small"
              />
              <Text strong className="text-xs">
                open &gt; {STALE_DAYS}d
              </Text>
              <Icons.ArrowRight size={12} color={token.colorWarning} />
            </RouterLink>
          )}

          <div className={styles.attentionBlock}>
            <Text strong className="mb-2 block text-xs">
              Groups needing attention
            </Text>
            {metrics.topBlocked.length === 0 ? (
              <Text type="secondary" className="text-sm">
                No stalled or high-risk assessments.
              </Text>
            ) : (
              <Flex vertical gap={4}>
                {metrics.topBlocked.map((group) => (
                  <Flex
                    key={group.name}
                    justify="space-between"
                    align="center"
                    gap={12}
                    className={styles.blockedRow}
                  >
                    <Text className="truncate text-sm">{group.name}</Text>
                    <Flex gap={6} align="center" className="shrink-0">
                      {group.highRiskCount > 0 && (
                        <Tooltip title="High-risk assessments in this group">
                          <Badge
                            count={group.highRiskCount}
                            color={token.colorError}
                            size="small"
                          />
                        </Tooltip>
                      )}
                      {group.staleCount > 0 && (
                        <Tooltip
                          title={`Stalled (open > ${STALE_DAYS} days) in this group`}
                        >
                          <Badge
                            count={group.staleCount}
                            color={token.colorWarning}
                            size="small"
                          />
                        </Tooltip>
                      )}
                    </Flex>
                  </Flex>
                ))}
              </Flex>
            )}
          </div>
        </Flex>
      </Flex>
    </Card>
  );
};
