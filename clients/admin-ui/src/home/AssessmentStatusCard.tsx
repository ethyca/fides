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

import { RouterLink } from "~/features/common/nav/RouterLink";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import {
  type AssessmentSummarySegment,
  useGetPrivacyAssessmentSummaryQuery,
} from "~/features/privacy-assessments";

import styles from "./AssessmentStatusCard.module.scss";

type SegmentConfig = StackedBarSegment & { key: AssessmentSummarySegment };

const SEGMENTS: readonly SegmentConfig[] = [
  { key: "completed", color: "colorSuccess", label: "Completed" },
  { key: "pending", color: "colorInfo", label: "Pending" },
  { key: "open", color: "colorWarning", label: "Open" },
  { key: "risk", color: "colorError", label: "Risk" },
];

export const AssessmentStatusCard = () => {
  const { token } = antTheme.useToken();
  const { data: summary, isLoading } = useGetPrivacyAssessmentSummaryQuery();

  const total = summary?.total ?? 0;
  const bySegment = summary?.by_segment;
  const blockedGroups = summary?.blocked_groups ?? [];
  const owners = summary?.owners ?? [];

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
          {total === 0 || !bySegment ? (
            <div className={styles.segmentBarEmpty} />
          ) : (
            <StackedBarChart data={{ "": bySegment }} segments={SEGMENTS} />
          )}
          <Flex gap="large" wrap="wrap">
            {SEGMENTS.map(({ key, color, label }) => {
              const count = bySegment?.[key] ?? 0;
              return (
                <RouterLink
                  key={key}
                  unstyled
                  href={PRIVACY_ASSESSMENTS_ROUTE}
                  className={styles.segmentLegend}
                  aria-label={`${count} ${label} assessments`}
                >
                  <span
                    className={styles.segmentDot}
                    style={{ backgroundColor: token[color] }}
                  />
                  <Text strong className="text-sm">
                    {count}
                  </Text>
                  <Text type="secondary" className="text-sm">
                    {label}
                  </Text>
                </RouterLink>
              );
            })}
          </Flex>
        </Flex>

        <div className={styles.attentionGrid}>
          <div className={styles.attentionColumn}>
            <Text strong className="mb-2 block text-xs">
              Purposes needing attention
            </Text>
            {blockedGroups.length === 0 ? (
              <Text type="secondary" className="text-sm">
                No out-of-date or high-risk assessments.
              </Text>
            ) : (
              <Flex vertical gap={2} className={styles.attentionList}>
                {blockedGroups.map((group) => {
                  const parts: string[] = [];
                  if (group.high_risk_count > 0) {
                    parts.push(`${group.high_risk_count} risk`);
                  }
                  if (group.outdated_count > 0) {
                    parts.push(`${group.outdated_count} out of date`);
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
            {owners.length === 0 ? (
              <Text type="secondary" className="text-sm">
                No open assessments assigned.
              </Text>
            ) : (
              <Flex vertical gap={2} className={styles.attentionList}>
                {owners.map((owner) => (
                  <RouterLink
                    key={owner.owner}
                    unstyled
                    href={PRIVACY_ASSESSMENTS_ROUTE}
                    className={styles.attentionRow}
                  >
                    <Text className="truncate text-sm">{owner.owner}</Text>
                    <Text type="secondary" className="shrink-0 text-xs">
                      {owner.open_count} open
                      {owner.outdated_count > 0
                        ? ` · ${owner.outdated_count} out of date`
                        : ""}
                    </Text>
                  </RouterLink>
                ))}
              </Flex>
            )}
          </div>
        </div>
      </Flex>
    </Card>
  );
};
