import { antTheme, Card, Flex, Icons, Text, Tooltip } from "fidesui";
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
const TOP_OWNERS_LIMIT = 3;

type SegmentKey = "completed" | "pending" | "open" | "risk";

interface SegmentDefinition {
  key: SegmentKey;
  label: string;
  colorToken: "colorSuccess" | "colorInfo" | "colorWarning" | "colorError";
  href: string;
}

const SEGMENTS: SegmentDefinition[] = [
  {
    key: "completed",
    label: "Completed",
    colorToken: "colorSuccess",
    href: `${PRIVACY_ASSESSMENTS_ROUTE}?status=${AssessmentStatus.COMPLETED}`,
  },
  {
    key: "pending",
    label: "Pending",
    colorToken: "colorInfo",
    href: `${PRIVACY_ASSESSMENTS_ROUTE}?status=${AssessmentStatus.GENERATING}`,
  },
  {
    key: "open",
    label: "Open",
    colorToken: "colorWarning",
    href: `${PRIVACY_ASSESSMENTS_ROUTE}?status=${AssessmentStatus.IN_PROGRESS}`,
  },
  {
    key: "risk",
    label: "Risk",
    colorToken: "colorError",
    href: `${PRIVACY_ASSESSMENTS_ROUTE}?status=${AssessmentStatus.IN_PROGRESS}`,
  },
];

interface BlockedGroup {
  name: string;
  dataUse: string | null;
  staleCount: number;
  highRiskCount: number;
  totalCount: number;
}

interface OwnerStat {
  owner: string;
  openCount: number;
  staleCount: number;
}

interface AssessmentMetrics {
  total: number;
  bySegment: Record<SegmentKey, number>;
  topBlocked: BlockedGroup[];
  blockedGroupOverflow: number;
  topOwners: OwnerStat[];
  ownerOverflow: number;
}

const EMPTY_SEGMENT_COUNTS: Record<SegmentKey, number> = {
  completed: 0,
  pending: 0,
  open: 0,
  risk: 0,
};

function segmentForAssessment(
  assessment: PrivacyAssessmentResponse,
): SegmentKey {
  switch (assessment.status) {
    case AssessmentStatus.COMPLETED:
      return "completed";
    case AssessmentStatus.GENERATING:
      return "pending";
    default:
      return assessment.risk_level === RiskLevel.HIGH ? "risk" : "open";
  }
}

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
  const bySegment = { ...EMPTY_SEGMENT_COUNTS };
  const groupAgg = new Map<string, BlockedGroup>();
  let total = 0;

  const staleBefore = Date.now() - STALE_DAYS * 24 * 60 * 60 * 1000;

  const ownerAgg = new Map<string, OwnerStat>();

  groups?.forEach((group) => {
    const groupLabel = group.data_use_name ?? "Uncategorized";
    let agg = groupAgg.get(groupLabel);
    if (!agg) {
      agg = {
        name: groupLabel,
        dataUse: group.data_use ?? null,
        staleCount: 0,
        highRiskCount: 0,
        totalCount: 0,
      };
      groupAgg.set(groupLabel, agg);
    }

    group.assessments?.forEach((assessment) => {
      total += 1;
      agg!.totalCount += 1;
      bySegment[segmentForAssessment(assessment)] += 1;
      if (assessment.risk_level === RiskLevel.HIGH) {
        agg!.highRiskCount += 1;
      }
      const stale = isStale(assessment, staleBefore);
      if (stale) {
        agg!.staleCount += 1;
      }

      const isOpen =
        assessment.status === AssessmentStatus.IN_PROGRESS ||
        assessment.status === AssessmentStatus.OUTDATED;
      if (isOpen && assessment.created_by) {
        let owner = ownerAgg.get(assessment.created_by);
        if (!owner) {
          owner = {
            owner: assessment.created_by,
            openCount: 0,
            staleCount: 0,
          };
          ownerAgg.set(assessment.created_by, owner);
        }
        owner.openCount += 1;
        if (stale) {
          owner.staleCount += 1;
        }
      }
    });
  });

  const sortedBlocked = Array.from(groupAgg.values())
    .filter((g) => g.staleCount > 0 || g.highRiskCount > 0)
    .sort(
      (a, b) =>
        b.staleCount + b.highRiskCount - (a.staleCount + a.highRiskCount),
    );
  const topBlocked = sortedBlocked.slice(0, TOP_BLOCKED_LIMIT);
  const blockedGroupOverflow = Math.max(
    sortedBlocked.length - TOP_BLOCKED_LIMIT,
    0,
  );

  const sortedOwners = Array.from(ownerAgg.values()).sort(
    (a, b) => b.openCount - a.openCount,
  );
  const topOwners = sortedOwners.slice(0, TOP_OWNERS_LIMIT);
  const ownerOverflow = Math.max(sortedOwners.length - TOP_OWNERS_LIMIT, 0);

  return {
    total,
    bySegment,
    topBlocked,
    blockedGroupOverflow,
    topOwners,
    ownerOverflow,
  };
}

export const AssessmentStatusCard = () => {
  const { token } = antTheme.useToken();
  const { data, isLoading } = useGetPrivacyAssessmentsQuery();

  const metrics = useMemo(() => computeMetrics(data?.items), [data?.items]);

  return (
    <Card
      title={
        <Tooltip
          placement="bottom"
          title="A snapshot of your privacy assessments program — completion progress, in-flight work, and where risk lives."
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
      <Flex vertical gap="large">
        <Flex vertical gap={12}>
          <div className={styles.segmentBar}>
            {metrics.total === 0 ? (
              <div className={styles.segmentBarEmpty} />
            ) : (
              SEGMENTS.map(({ key, label, colorToken }) => {
                const value = metrics.bySegment[key];
                if (value === 0) {
                  return null;
                }
                return (
                  <Tooltip
                    key={key}
                    title={`${value} ${label}`}
                    placement="top"
                  >
                    <div
                      className={styles.segmentBarFill}
                      style={{
                        flex: value,
                        backgroundColor: token[colorToken],
                      }}
                    />
                  </Tooltip>
                );
              })
            )}
          </div>
          <Flex gap="large" wrap="wrap">
            {SEGMENTS.map(({ key, label, colorToken, href }) => (
              <RouterLink
                key={key}
                unstyled
                href={href}
                className={styles.segmentLegend}
              >
                <span
                  className={styles.segmentDot}
                  style={{ backgroundColor: token[colorToken] }}
                />
                <Text strong className="text-sm">
                  {metrics.bySegment[key]}
                </Text>
                <Text type="secondary" className="text-sm">
                  {label}
                </Text>
              </RouterLink>
            ))}
          </Flex>
        </Flex>

        <Flex gap="large" align="stretch" wrap="wrap">
          <div className={styles.attentionColumn}>
            <Text strong className="mb-2 block text-xs">
              Owners with open work
            </Text>
            {metrics.topOwners.length === 0 ? (
              <Text type="secondary" className="text-sm">
                No open assessments assigned.
              </Text>
            ) : (
              <Flex vertical gap={2}>
                {metrics.topOwners.map((owner) => (
                  <RouterLink
                    key={owner.owner}
                    unstyled
                    href={PRIVACY_ASSESSMENTS_ROUTE}
                    className={styles.attentionRow}
                  >
                    <Text className="truncate text-sm">{owner.owner}</Text>
                    <Text type="secondary" className="shrink-0 text-xs">
                      {owner.openCount} open
                      {owner.staleCount > 0
                        ? ` · ${owner.staleCount} stalled`
                        : ""}
                    </Text>
                  </RouterLink>
                ))}
                {metrics.ownerOverflow > 0 && (
                  <RouterLink
                    unstyled
                    href={PRIVACY_ASSESSMENTS_ROUTE}
                    className={styles.attentionOverflow}
                  >
                    <Text type="secondary" className="text-xs">
                      + {metrics.ownerOverflow} more owner
                      {metrics.ownerOverflow === 1 ? "" : "s"}
                    </Text>
                  </RouterLink>
                )}
              </Flex>
            )}
          </div>

          <div className={styles.attentionColumn}>
            <Text strong className="mb-2 block text-xs">
              Groups needing attention
            </Text>
            {metrics.topBlocked.length === 0 ? (
              <Text type="secondary" className="text-sm">
                No stalled or high-risk assessments.
              </Text>
            ) : (
              <Flex vertical gap={2}>
                {metrics.topBlocked.map((group) => {
                  const parts: string[] = [];
                  if (group.highRiskCount > 0) {
                    parts.push(`${group.highRiskCount} risk`);
                  }
                  if (group.staleCount > 0) {
                    parts.push(`${group.staleCount} stalled`);
                  }
                  return (
                    <RouterLink
                      key={group.name}
                      unstyled
                      href={PRIVACY_ASSESSMENTS_ROUTE}
                      className={styles.attentionRow}
                    >
                      <Text className="truncate text-sm">{group.name}</Text>
                      <Text type="secondary" className="shrink-0 text-xs">
                        {parts.join(" · ")}
                      </Text>
                    </RouterLink>
                  );
                })}
                {metrics.blockedGroupOverflow > 0 && (
                  <RouterLink
                    unstyled
                    href={PRIVACY_ASSESSMENTS_ROUTE}
                    className={styles.attentionOverflow}
                  >
                    <Text type="secondary" className="text-xs">
                      + {metrics.blockedGroupOverflow} more group
                      {metrics.blockedGroupOverflow === 1 ? "" : "s"}
                    </Text>
                  </RouterLink>
                )}
              </Flex>
            )}
          </div>
        </Flex>
      </Flex>
    </Card>
  );
};
