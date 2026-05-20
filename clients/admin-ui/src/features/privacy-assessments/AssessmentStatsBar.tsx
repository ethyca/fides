import { Divider, Flex, Text } from "fidesui";

import styles from "./AssessmentStatsBar.module.scss";
import {
  AssessmentStatus,
  AssessmentGroupResponse,
  RiskLevel,
} from "./types";

interface AssessmentStatsBarProps {
  groups: AssessmentGroupResponse[];
}

export const AssessmentStatsBar = ({ groups }: AssessmentStatsBarProps) => {
  const allAssessments = groups.flatMap((g) => g.assessments ?? []);
  const total = allAssessments.length;

  const needsInputCount = allAssessments.filter(
    (a) =>
      a.status === AssessmentStatus.IN_PROGRESS ||
      a.status === AssessmentStatus.OUTDATED,
  ).length;

  const agentDraftingCount = allAssessments.filter(
    (a) => a.status === AssessmentStatus.GENERATING,
  ).length;

  const highRiskCount = allAssessments.filter(
    (a) => a.risk_level === RiskLevel.HIGH,
  ).length;

  const signedCount = allAssessments.filter(
    (a) => a.status === AssessmentStatus.COMPLETED,
  ).length;

  // Slack gathering isn't directly derivable from current API data,
  // so we show 0 for now
  const slackCount = 0;

  const stats = [
    {
      label: "Needs your attention",
      value: needsInputCount,
      subtitle: "needs-input + ready-to-sign",
      color: "var(--fidesui-brand-terracotta)",
    },
    {
      label: "Agent · Drafting",
      value: agentDraftingCount,
    },
    {
      label: "Slack · Gathering",
      value: slackCount,
    },
    {
      label: "High-risk findings",
      value: highRiskCount,
      color: "var(--fidesui-color-error)",
    },
    {
      label: "Signed this quarter",
      value: signedCount,
      color: "var(--fidesui-color-success)",
    },
  ];

  if (total === 0) {
    return null;
  }

  return (
    <div className={styles.container}>
      <Flex>
        {stats.map((stat, i) => (
          <div key={stat.label} className={styles.cell}>
            <Text variant="monoLabel" type="secondary" size="sm" strong>
              {stat.label}
            </Text>
            <div
              className={styles.value}
              style={stat.color ? { color: stat.color } : undefined}
            >
              {String(stat.value).padStart(2, "0")}
            </div>
            {stat.subtitle && (
              <Text type="secondary" size="sm">
                {stat.subtitle}
              </Text>
            )}
          </div>
        ))}
      </Flex>
      <Divider className="mt-4 mb-0" />
    </div>
  );
};
