import { subDays } from "date-fns";
import {
  antTheme,
  Card,
  Flex,
  Icons,
  StackedBarChart,
  type StackedBarSegment,
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

// TODO: replace with a `/privacy-assessments/summary` endpoint — fetching the
// full list to render counters and top-3 lists is wasteful at scale.
const STALE_DAYS = 14;
const TOP_OWNERS_LIMIT = 3;
const UNCATEGORIZED_KEY = "__uncategorized__";

type SegmentKey = "completed" | "pending" | "open" | "risk";

const SEGMENTS: readonly StackedBarSegment[] = [
  { key: "completed", color: "colorSuccess", label: "Completed" },
  { key: "pending", color: "colorInfo", label: "Pending" },
  { key: "open", color: "colorWarning", label: "Open" },
  { key: "risk", color: "colorError", label: "Risk" },
];

interface BlockedGroup {
  name: string;
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
  blockedGroups: BlockedGroup[];
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
    case AssessmentStatus.IN_PROGRESS:
    case AssessmentStatus.OUTDATED:
      return assessment.risk_level === RiskLevel.HIGH ? "risk" : "open";
    default: {
      const exhaustive: never = assessment.status;
      return exhaustive;
    }
  }
}

// Only IN_PROGRESS / OUTDATED can be stale; COMPLETED and GENERATING never are.
function isStale(
  assessment: PrivacyAssessmentResponse,
  staleBefore: number,
): boolean {
  if (
    assessment.status === AssessmentStatus.COMPLETED ||
    assessment.status === AssessmentStatus.GENERATING ||
    !assessment.updated_at
  ) {
    return false;
  }
  return new Date(assessment.updated_at).getTime() < staleBefore;
}

function computeMetrics(
  groups: AssessmentGroupResponse[] | undefined,
  now: number = Date.now(),
): AssessmentMetrics {
  const bySegment = { ...EMPTY_SEGMENT_COUNTS };
  const groupAgg = new Map<string, BlockedGroup>();
  const ownerAgg = new Map<string, OwnerStat>();
  let total = 0;

  const staleBefore = subDays(now, STALE_DAYS).getTime();

  groups?.forEach((group) => {
    const groupKey = group.data_use ?? UNCATEGORIZED_KEY;
    let aggregate = groupAgg.get(groupKey);
    if (!aggregate) {
      aggregate = {
        name: group.data_use_name ?? "Uncategorized",
        staleCount: 0,
        highRiskCount: 0,
        totalCount: 0,
      };
      groupAgg.set(groupKey, aggregate);
    }

    group.assessments?.forEach((assessment) => {
      total += 1;
      aggregate!.totalCount += 1;
      bySegment[segmentForAssessment(assessment)] += 1;
      if (assessment.risk_level === RiskLevel.HIGH) {
        aggregate!.highRiskCount += 1;
      }
      const stale = isStale(assessment, staleBefore);
      if (stale) {
        aggregate!.staleCount += 1;
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

  const blockedGroups = Array.from(groupAgg.values())
    .filter((g) => g.staleCount > 0 || g.highRiskCount > 0)
    .sort(
      (a, b) =>
        b.staleCount + b.highRiskCount - (a.staleCount + a.highRiskCount),
    );

  const sortedOwners = Array.from(ownerAgg.values()).sort(
    (a, b) => b.openCount - a.openCount,
  );
  const topOwners = sortedOwners.slice(0, TOP_OWNERS_LIMIT);
  const ownerOverflow = Math.max(sortedOwners.length - TOP_OWNERS_LIMIT, 0);

  return {
    total,
    bySegment,
    blockedGroups,
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
        <Flex style={{ display: "inline-flex" }} align="center" gap={4}>
          <Text>Assessment Status</Text>
          <Tooltip
            placement="bottom"
            title="A snapshot of your privacy assessments program — completion progress, in-flight work, and where risk lives."
          >
            <Icons.Help
              size={14}
              className="opacity-30"
              style={{ cursor: "help" }}
            />
          </Tooltip>
        </Flex>
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
      <Flex vertical gap="large" className="min-h-0 flex-1">
        <Flex vertical gap={12}>
          {metrics.total === 0 ? (
            <div className={styles.segmentBarEmpty} />
          ) : (
            <StackedBarChart
              data={{ "": metrics.bySegment }}
              segments={SEGMENTS}
            />
          )}
          <Flex gap="large" wrap="wrap">
            {SEGMENTS.map(({ key, color, label }) => (
              <RouterLink
                key={key}
                unstyled
                href={PRIVACY_ASSESSMENTS_ROUTE}
                className={styles.segmentLegend}
              >
                <span
                  className={styles.segmentDot}
                  style={{ backgroundColor: token[color] }}
                />
                <Text strong className="text-sm">
                  {metrics.bySegment[key as SegmentKey]}
                </Text>
                <Text type="secondary" className="text-sm">
                  {label}
                </Text>
              </RouterLink>
            ))}
          </Flex>
        </Flex>

        <div className={styles.attentionGrid}>
          <div className={styles.attentionColumn}>
            <Text strong className="mb-2 block text-xs">
              Purposes
            </Text>
            {metrics.blockedGroups.length === 0 ? (
              <Text type="secondary" className="text-sm">
                No stalled or high-risk assessments.
              </Text>
            ) : (
              <Flex vertical gap={2} className={styles.attentionList}>
                {metrics.blockedGroups.map((group) => {
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
              </Flex>
            )}
          </div>

          <div className={styles.attentionColumn}>
            <Text strong className="mb-2 block text-xs">
              Owners with open work
            </Text>
            {metrics.topOwners.length === 0 ? (
              <Text type="secondary" className="text-sm">
                No open assessments assigned.
              </Text>
            ) : (
              <Flex vertical gap={2} className={styles.attentionList}>
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
        </div>
      </Flex>
    </Card>
  );
};
