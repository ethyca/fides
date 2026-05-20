import {
  Avatar,
  Button,
  Card,
  Flex,
  SegmentedProgress,
  Spin,
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
import {
  RISK_LEVEL_DOT_COLORS,
  RISK_LEVEL_LABELS,
  STATUS_BADGE_COLORS,
  STATUS_BADGE_LABELS,
} from "./constants";
import {
  AssessmentStatus,
  PrivacyAssessmentResponse,
  RiskLevel,
} from "./types";

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

  const statusLabel = status ? STATUS_BADGE_LABELS[status] : null;
  const statusColor = status ? STATUS_BADGE_COLORS[status] : undefined;
  const riskLabel = riskLevel ? RISK_LEVEL_LABELS[riskLevel] : null;
  const riskDotColor = riskLevel ? RISK_LEVEL_DOT_COLORS[riskLevel] : undefined;

  const systemName = assessment.system_name ?? "Unknown system";
  const systemInitial = systemName.charAt(0).toUpperCase();
  const connectionLogo = connectionLogoFromAssessment(assessment);

  // Derive a regulation/region subtitle from the template name
  // e.g., "GDPR Data Protection Impact Assessment (DPIA)" → "GDPR DPIA"
  const templateName = assessment.template_name ?? assessment.name;

  // The list API only provides completeness as a percentage, not discrete counts.
  // Use a fixed segment count to approximate the segmented bar.
  const PROGRESS_SEGMENTS = 20;
  const filledSegments = Math.round((completeness / 100) * PROGRESS_SEGMENTS);

  const actionLabel = isGenerating ? null : isComplete ? "View" : "Resume";

  // Data categories as display items
  const dataCategories = (assessment.data_categories ?? []).map((key) => ({
    key,
    label: getDataCategoryDisplayName(key),
  }));

  return (
    <Card variant="borderless" className={styles.card}>
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
              <span
                className={styles.statusDot}
                style={{ backgroundColor: statusColor }}
              />
              <Text variant="monoLabel" size="sm" strong>
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

        {/* Risk level */}
        {riskLabel && (
          <Flex align="center" gap={6}>
            <span
              className={styles.riskDot}
              style={{
                backgroundColor: riskDotColor,
                boxShadow:
                  riskLevel === RiskLevel.HIGH
                    ? `0 0 6px ${riskDotColor}`
                    : undefined,
              }}
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
        )}

        {/* Spacer to push progress to bottom */}
        <div className="flex-1" />

        {/* Progress section */}
        {isGenerating ? (
          <Flex align="center" justify="center" gap="small" className="py-2">
            <Spin size="small" />
            <Text type="secondary" size="sm">
              Generating this assessment
            </Text>
          </Flex>
        ) : (
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
              total={PROGRESS_SEGMENTS}
              filled={filledSegments}
            />
          </div>
        )}

        {/* Bottom row: action button */}
        {actionLabel && (
          <Flex justify="flex-end" align="center">
            <Button type="link" className="p-0" onClick={onClick}>
              {actionLabel} →
            </Button>
          </Flex>
        )}
      </Flex>
    </Card>
  );
};
