import { Button, Card, Col, Flex, Row, Text, Typography } from "fidesui";
import { useRouter } from "next/router";
import { useState } from "react";

import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";

import { AssessmentCard } from "./AssessmentCard";
import styles from "./AssessmentGroup.module.scss";
import { RISK_LEVEL_DOT_COLORS, RISK_LEVEL_LABELS } from "./constants";
import {
  AssessmentStatus,
  PrivacyAssessmentResponse,
  RiskLevel,
} from "./types";

const { Title } = Typography;

interface AssessmentGroupProps {
  /** Zero-padded row index, e.g., "01" */
  index: number;
  dataUseName: string | null;
  assessments?: PrivacyAssessmentResponse[];
  /** Max cards to show before overflow. */
  maxVisible?: number;
}

function getHighestRisk(
  assessments: PrivacyAssessmentResponse[],
): RiskLevel | null {
  const priority = [RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW];
  return (
    priority.find((level) => assessments.some((a) => a.risk_level === level)) ??
    null
  );
}

export const AssessmentGroup = ({
  index,
  dataUseName,
  assessments = [],
  maxVisible = 4,
}: AssessmentGroupProps) => {
  const router = useRouter();
  const [expanded, setExpanded] = useState(false);

  const displayName = dataUseName ?? "Uncategorized";
  const rowNumber = String(index + 1).padStart(2, "0");

  // Compute summary stats
  const totalAssessments = assessments.length;
  const needsInputCount = assessments.filter(
    (a) => a.status === AssessmentStatus.IN_PROGRESS,
  ).length;
  const avgAnswered =
    totalAssessments > 0
      ? Math.round(
          assessments.reduce((sum, a) => sum + (a.completeness ?? 0), 0) /
            totalAssessments,
        )
      : 0;
  const highestRisk = getHighestRisk(assessments);

  // Overflow logic
  const showOverflow = !expanded && assessments.length > maxVisible;
  const visibleAssessments = showOverflow
    ? assessments.slice(0, maxVisible)
    : assessments;
  const overflowCount = assessments.length - maxVisible;

  // Category label for cards (short version of the data use)
  const categoryLabel = dataUseName?.split(" ")[0]?.toUpperCase() ?? undefined;
  // Parent category for the header kicker (e.g. "Privacy · Analytics")
  const headerCategory = dataUseName?.split(" ")[0] ?? displayName;

  return (
    <div>
      {/* Group header */}
      <Flex
        justify="space-between"
        align="flex-end"
        gap={16}
        className={`mb-4 ${styles.header}`}
      >
        <Flex gap={12} align="flex-end" flex="1 1 auto" style={{ minWidth: 0 }}>
          <Text type="secondary" className={styles.rowNumber}>
            {rowNumber}
          </Text>
          <div>
            <Text variant="monoLabel" type="secondary" size="sm" strong>
              Privacy · {headerCategory}
            </Text>
            <Title level={2} className={`!m-0 ${styles.groupTitle}`}>
              {displayName}
            </Title>
          </div>
        </Flex>

        {/* Right-side summary stats */}
        <Flex gap={24} align="baseline">
          <div className={styles.statCell}>
            <Text variant="monoLabel" type="secondary" size="sm">
              Assessments
            </Text>
            <Text className={styles.statValue}>
              {String(totalAssessments).padStart(2, "0")}
            </Text>
          </div>
          <div className={styles.statCell}>
            <Text variant="monoLabel" type="secondary" size="sm">
              Needs input
            </Text>
            <Text
              className={styles.statValue}
              style={
                needsInputCount > 0
                  ? { color: "var(--fidesui-brand-terracotta)" }
                  : undefined
              }
            >
              {String(needsInputCount).padStart(2, "0")}
            </Text>
          </div>
          <div className={styles.statCell}>
            <Text variant="monoLabel" type="secondary" size="sm">
              Avg · Answered
            </Text>
            <Text className={styles.statValue}>{avgAnswered}%</Text>
          </div>
          <div className={styles.statCell}>
            <Text variant="monoLabel" type="secondary" size="sm">
              Highest risk
            </Text>
            <Text
              className={styles.statValue}
              style={
                highestRisk
                  ? { color: RISK_LEVEL_DOT_COLORS[highestRisk] }
                  : undefined
              }
            >
              {highestRisk ? RISK_LEVEL_LABELS[highestRisk] : "—"}
            </Text>
          </div>
        </Flex>
      </Flex>

      {/* Card grid */}
      <Row gutter={[16, 16]}>
        {visibleAssessments.map((assessment) => (
          <Col key={assessment.id} span={6}>
            <AssessmentCard
              assessment={assessment}
              categoryLabel={categoryLabel}
              onClick={() =>
                router.push(`${PRIVACY_ASSESSMENTS_ROUTE}/${assessment.id}`)
              }
            />
          </Col>
        ))}
        {showOverflow && (
          <Col span={6}>
            <Card variant="borderless" className={styles.overflowCard}>
              <Flex
                vertical
                align="center"
                justify="center"
                className="h-full"
                gap={4}
              >
                <Text className={styles.overflowNumber}>+ {overflowCount}</Text>
                <Text variant="monoLabel" type="secondary" size="sm" strong>
                  More assessments
                </Text>
                <Button
                  type="link"
                  className="p-0"
                  onClick={() => setExpanded(true)}
                >
                  Show all →
                </Button>
              </Flex>
            </Card>
          </Col>
        )}
      </Row>
    </div>
  );
};
