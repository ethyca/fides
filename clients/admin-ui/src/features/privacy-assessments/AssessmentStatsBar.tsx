import classNames from "classnames";
import { Divider, Flex, Text } from "fidesui";

import styles from "./AssessmentStatsBar.module.scss";
import {
  AssessmentGroupResponse,
  DerivedAssessmentStatus,
  RiskLevel,
} from "./types";
import { deriveAssessmentStatus } from "./utils";

interface AssessmentStatsBarProps {
  groups: AssessmentGroupResponse[];
}

export const AssessmentStatsBar = ({ groups }: AssessmentStatsBarProps) => {
  const allAssessments = groups.flatMap((g) => g.assessments ?? []);
  const total = allAssessments.length;

  const countsByDerived = new Map<DerivedAssessmentStatus, number>();
  allAssessments.forEach((a) => {
    const key = deriveAssessmentStatus(a);
    countsByDerived.set(key, (countsByDerived.get(key) ?? 0) + 1);
  });
  const countOf = (key: DerivedAssessmentStatus) =>
    countsByDerived.get(key) ?? 0;

  // "Needs your attention" covers cards waiting on the human reviewer:
  // ``IN_PROGRESS`` (open answers), ``OUTDATED`` (re-check needed), and
  // ``SLACK_STOPPED`` (questionnaire bailed, follow-up required).
  // ``SLACK_GATHERING`` is excluded — the agent is waiting on the SME.
  const needsInputCount =
    countOf(DerivedAssessmentStatus.IN_PROGRESS) +
    countOf(DerivedAssessmentStatus.OUTDATED) +
    countOf(DerivedAssessmentStatus.SLACK_STOPPED);

  const agentDraftingCount = countOf(DerivedAssessmentStatus.GENERATING);
  const slackCount = countOf(DerivedAssessmentStatus.SLACK_GATHERING);
  const signedCount = countOf(DerivedAssessmentStatus.COMPLETED);

  const highRiskCount = allAssessments.filter(
    (a) => a.risk_level === RiskLevel.HIGH,
  ).length;

  const stats = [
    {
      label: "Needs your attention",
      value: needsInputCount,
      subtitle: "needs-input + ready-to-sign",
      color: "var(--fidesui-brand-terracotta)",
      featured: true,
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
        {stats.map((stat) => (
          <div key={stat.label} className={styles.cell}>
            <Text variant="monoLabel" type="secondary" size="sm" strong>
              {stat.label}
            </Text>
            <div
              className={classNames(styles.value, {
                [styles.featured]: stat.featured,
              })}
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
      <Divider className="mb-0 mt-4" />
    </div>
  );
};
