import type { AntColorTokenKey } from "fidesui";
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

// Threshold for flagging an open assessment as "stalled" in the per-group and
// per-owner attention rows. Frontend-only heuristic; revisit if the privacy
// team defines a formal SLA.
// TODO: replace `useGetPrivacyAssessmentsQuery()` here with a dedicated
// /privacy-assessments/summary endpoint once available — fetching the full
// dataset just to produce 4 counters and two top-3 lists is wasteful at scale.
const STALE_DAYS = 14;
const TOP_OWNERS_LIMIT = 3;
const UNCATEGORIZED_KEY = "__uncategorized__";

type SegmentKey = "completed" | "pending" | "open" | "risk";

interface SegmentDefinition {
  key: SegmentKey;
  label: string;
  colorToken: AntColorTokenKey;
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
    href: `${PRIVACY_ASSESSMENTS_ROUTE}?status=${AssessmentStatus.IN_PROGRESS}&risk_level=${RiskLevel.HIGH}`,
  },
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

export interface AssessmentMetrics {
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
    default:
      return assessment.risk_level === RiskLevel.HIGH ? "risk" : "open";
  }
}

function isStale(
  assessment: PrivacyAssessmentResponse,
  staleBefore: number,
): boolean {
  // GENERATING rows are still being produced by the backend; treat them as
  // fresh regardless of timestamps. COMPLETED rows are never stale.
  if (
    assessment.status === AssessmentStatus.COMPLETED ||
    assessment.status === AssessmentStatus.GENERATING
  ) {
    return false;
  }
  if (!assessment.updated_at) {
    return false;
  }
  const updatedAt = new Date(assessment.updated_at).getTime();
  return Number.isFinite(updatedAt) && updatedAt < staleBefore;
}

function getOrInsert<K, V>(map: Map<K, V>, key: K, factory: () => V): V {
  const existing = map.get(key);
  if (existing) {
    return existing;
  }
  const created = factory();
  map.set(key, created);
  return created;
}

export function computeMetrics(
  groups: AssessmentGroupResponse[] | undefined,
  now: number = Date.now(),
): AssessmentMetrics {
  const bySegment = { ...EMPTY_SEGMENT_COUNTS };
  const groupAgg = new Map<string, BlockedGroup>();
  const ownerAgg = new Map<string, OwnerStat>();
  let total = 0;

  const staleBefore = now - STALE_DAYS * 24 * 60 * 60 * 1000;

  groups?.forEach((group) => {
    const groupKey = group.data_use ?? UNCATEGORIZED_KEY;
    const groupName = group.data_use_name ?? "Uncategorized";
    const aggregate = getOrInsert(groupAgg, groupKey, () => ({
      name: groupName,
      staleCount: 0,
      highRiskCount: 0,
      totalCount: 0,
    }));

    group.assessments?.forEach((assessment) => {
      total += 1;
      aggregate.totalCount += 1;
      bySegment[segmentForAssessment(assessment)] += 1;
      if (assessment.risk_level === RiskLevel.HIGH) {
        aggregate.highRiskCount += 1;
      }
      const stale = isStale(assessment, staleBefore);
      if (stale) {
        aggregate.staleCount += 1;
      }

      const isOpen =
        assessment.status === AssessmentStatus.IN_PROGRESS ||
        assessment.status === AssessmentStatus.OUTDATED;
      if (isOpen && assessment.created_by) {
        const owner = getOrInsert(ownerAgg, assessment.created_by, () => ({
          owner: assessment.created_by!,
          openCount: 0,
          staleCount: 0,
        }));
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
