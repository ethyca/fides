import {
  Avatar,
  Button,
  Card,
  FidesIndicator,
  Flex,
  SegmentedProgress,
  Text,
  Typography,
} from "fidesui";

import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { RouterLink } from "~/features/common/nav/RouterLink";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import ConnectionTypeLogo, {
  connectionLogoFromAssessment,
} from "~/features/datastore-connections/ConnectionTypeLogo";

import styles from "./AssessmentCard.module.scss";
import { AssessmentProgressLegend } from "./AssessmentProgressLegend";
import {
  RISK_LEVEL_DOT_COLORS,
  RISK_LEVEL_LABELS,
  STATUS_BADGE_COLORS,
  STATUS_BADGE_LABELS,
} from "./constants";
import {
  AssessmentStatus,
  DerivedAssessmentStatus,
  PrivacyAssessmentResponse,
  RiskLevel,
} from "./types";
import {
  ANSWER_SOURCE_BUCKET_COLORS,
  deriveAssessmentStatus,
  groupAnswersBySource,
} from "./utils";

const { Title } = Typography;

interface AssessmentCardProps {
  assessment: PrivacyAssessmentResponse;
  /** The data-use category label for the top-left monoLabel. */
  categoryLabel?: string;
  onClick: () => void;
}

export const AssessmentCard = ({
  assessment,
  categoryLabel,
  onClick,
}: AssessmentCardProps) => {
  const { getDataCategoryDisplayName } = useTaxonomies();

  const riskLevel = assessment.risk_level ?? null;
  const status = assessment.status ?? null;
  const completeness = assessment.completeness ?? 0;
  const isGenerating = status === AssessmentStatus.GENERATING;
  const isComplete = status === AssessmentStatus.COMPLETED;

  // Single source of truth for what the badge should show — combines
  // ``status`` with orthogonal signals (e.g. ``questionnaire_status``).
  // See ``deriveAssessmentStatus`` for the resolution rules.
  const derivedStatus = deriveAssessmentStatus(assessment);
  const statusLabel = STATUS_BADGE_LABELS[derivedStatus];
  const statusColor = STATUS_BADGE_COLORS[derivedStatus];
  const isAgentActive =
    derivedStatus === DerivedAssessmentStatus.GENERATING ||
    derivedStatus === DerivedAssessmentStatus.SLACK_GATHERING;
  const riskLabel = riskLevel ? RISK_LEVEL_LABELS[riskLevel] : null;
  const riskDotColor = riskLevel ? RISK_LEVEL_DOT_COLORS[riskLevel] : undefined;

  const systemName = assessment.system_name ?? "Unknown system";
  const systemInitial = systemName.charAt(0).toUpperCase();
  const connectionLogo = connectionLogoFromAssessment(assessment);

  // Derive a regulation/region subtitle from the template name
  // e.g., "GDPR Data Protection Impact Assessment (DPIA)" → "GDPR DPIA"
  const templateName = assessment.template_name ?? assessment.name;

  // Use the per-source breakdown when the backend supplies it; the
  // bar shows one coloured run per Agent / Slack / Manual bucket.
  // ``total_questions`` is the bar's denominator; ``completeness`` is still
  // shown as the percentage label.
  const groupedAnswers = groupAnswersBySource(assessment.answered_by);
  const totalQuestions = assessment.total_questions ?? 0;
  const progressSegments = [
    {
      color: ANSWER_SOURCE_BUCKET_COLORS.agent,
      count: groupedAnswers.agent,
    },
    {
      color: ANSWER_SOURCE_BUCKET_COLORS.slack,
      count: groupedAnswers.slack,
    },
    {
      color: ANSWER_SOURCE_BUCKET_COLORS.manual,
      count: groupedAnswers.manual,
    },
  ];

  let actionLabel = "Resume";
  if (isComplete || isGenerating) {
    actionLabel = "View";
  }

  // Data categories as display items
  const dataCategories = (assessment.data_categories ?? []).map((key) => ({
    key,
    label: getDataCategoryDisplayName(key),
  }));

  return (
    <Card
      variant="borderless"
      className={`${styles.card} ${
        derivedStatus === DerivedAssessmentStatus.IN_PROGRESS
          ? styles.cardNeedsInput
          : ""
      }`}
    >
      <Flex vertical gap={12} className="flex-1">
        {/* Top row: category label + status badge */}
        <Flex justify="space-between" align="center">
          {categoryLabel && (
            <Text variant="monoLabel" type="secondary" strong>
              {categoryLabel}
            </Text>
          )}
          {statusLabel && (
            <Flex align="center" gap={6} className={styles.statusBadge}>
              <FidesIndicator
                color={statusColor}
                pulsating={isAgentActive}
                className="mb-0.5"
              />
              <Text
                variant="monoLabel"
                size="sm"
                strong
                style={{ color: statusColor }}
              >
                {statusLabel}
              </Text>
            </Flex>
          )}
        </Flex>

        {/* System row: avatar + name + template subtitle */}
        <Flex gap={8} align="flex-start">
          {connectionLogo ? (
            <ConnectionTypeLogo
              data={connectionLogo}
              size={24}
              className={styles.systemAvatar}
            />
          ) : (
            <Avatar shape="square" size={24} className={styles.systemAvatar}>
              {systemInitial}
            </Avatar>
          )}
          <div>
            <Title level={3} className="!m-0">
              {isGenerating ? (
                systemName
              ) : (
                <RouterLink
                  unstyled
                  href={`${PRIVACY_ASSESSMENTS_ROUTE}/${assessment.id}`}
                  className={styles.titleLink}
                >
                  {systemName}
                </RouterLink>
              )}
            </Title>
            <Text
              variant="monoLabel"
              size="sm"
              className={styles.templateSubtitle}
              strong
            >
              {templateName}
            </Text>
          </div>
        </Flex>

        {/* Data categories as text lines */}
        {dataCategories.length > 0 && (
          <div className={styles.dataCategoriesBlock}>
            {dataCategories.slice(0, 3).map((cat) => (
              <div key={cat.key} className={styles.dataCategoryLine}>
                <Text size="sm">{cat.label}</Text>
              </div>
            ))}
            {dataCategories.length > 3 && (
              <Text size="sm" type="secondary">
                +{dataCategories.length - 3} more
              </Text>
            )}
          </div>
        )}

        {/* Risk level — placeholder pulse while the agent is still assessing. */}
        {isGenerating ? (
          <Flex align="center" gap={6}>
            <FidesIndicator
              color="var(--fidesui-color-text-secondary)"
              pulsating
            />
            <Text variant="monoLabel" size="sm" strong type="secondary">
              Assessing risk
            </Text>
          </Flex>
        ) : (
          riskLabel && (
            <Flex align="center" gap={6}>
              <FidesIndicator
                color={riskDotColor}
                glowing={riskLevel === RiskLevel.HIGH}
              />
              <Text
                variant="monoLabel"
                size="sm"
                strong
                style={{ color: riskDotColor }}
              >
                {riskLabel} risk
              </Text>
            </Flex>
          )
        )}

        {/* Spacer to push progress to bottom */}
        <div className="flex-1" />

        {/* Progress section */}
        <div>
          <Flex justify="space-between" align="center" className="mb-1">
            <Text variant="monoLabel" type="secondary" size="sm" strong>
              Questions answered
            </Text>
            <Text variant="monoLabel" size="sm" strong>
              {Math.round(completeness)}%
            </Text>
          </Flex>
          <SegmentedProgress
            loading={isGenerating}
            total={totalQuestions}
            segments={progressSegments}
          />
          <Flex justify="flex-start" align="center" className="mt-2">
            <AssessmentProgressLegend breakdown={groupedAnswers} compact />
          </Flex>
        </div>

        {/* Bottom row: action button */}
        <Flex justify="flex-end" align="center" className="mt-[-30px]">
          <Button type="link" className="p-0" onClick={onClick}>
            {actionLabel} →
          </Button>
        </Flex>
      </Flex>
    </Card>
  );
};
