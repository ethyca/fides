import classNames from "classnames";
import {
  Button,
  Card,
  CUSTOM_TAG_COLOR,
  Flex,
  IconBadge,
  Icons,
  Progress,
  Tag,
  TagList,
  Text,
  Typography,
} from "fidesui";

import useTaxonomies from "~/features/common/hooks/useTaxonomies";

import styles from "./AssessmentCard.module.scss";
import {
  ASSESSMENT_STATUS_LABELS,
  RISK_LEVEL_LABELS,
  RISK_TAG_COLORS,
} from "./constants";
import { PrivacyAssessmentResponse } from "./types";

const { Title } = Typography;

function getStatusTextType(
  status: string | null,
): "success" | "danger" | "secondary" {
  if (status === "completed") {
    return "success";
  }
  if (status === "outdated") {
    return "danger";
  }
  return "secondary";
}

interface AssessmentCardProps {
  assessment: PrivacyAssessmentResponse;
  onClick: () => void;
}

export const AssessmentCard = ({
  assessment,
  onClick,
}: AssessmentCardProps) => {
  const { getDataCategoryDisplayName } = useTaxonomies();

  // Do not assume defaults for missing values; show "N/A" when absent
  const riskLevel = assessment.risk_level ?? null;
  const status = assessment.status ?? null;
  const completeness = assessment.completeness ?? 0;

  const riskLabel = riskLevel ? RISK_LEVEL_LABELS[riskLevel] : "N/A";
  const statusLabel = status ? ASSESSMENT_STATUS_LABELS[status] : "N/A";
  const isComplete = completeness === 100;

  return (
    <Card
      className={classNames(styles.cardWrapper, {
        [styles.cardComplete]: isComplete,
      })}
    >
      <Flex vertical gap="small" justify="space-between">
        <Title level={5}>{assessment.name}</Title>
        <Text type="secondary" className={styles.secondaryText}>
          System: {assessment.system_name ?? ""}
        </Text>
        <Text type="secondary" className={styles.textWithTags}>
          Processing{" "}
          {(assessment.data_categories ?? []).length > 0 ? (
            <TagList
              tags={(assessment.data_categories ?? []).map((key) => ({
                value: key,
                label: getDataCategoryDisplayName(key),
              }))}
              maxTags={1}
              expandable
            />
          ) : (
            <Tag>0 data categories</Tag>
          )}{" "}
          for{" "}
          <TagList
            tags={assessment.data_use_name ? [assessment.data_use_name] : []}
            maxTags={1}
          />
        </Text>
        {riskLevel && (
          <Tag color={RISK_TAG_COLORS[riskLevel] ?? CUSTOM_TAG_COLOR.DEFAULT}>
            {`${riskLabel} risk`}
          </Tag>
        )}

        <div className={styles.separator}>
          {isComplete ? (
            <Flex
              align="center"
              gap="middle"
              className={styles.completeContainer}
            >
              <IconBadge
                shape="circle"
                variant="filled"
                color="var(--fidesui-success)"
                size={28}
              >
                <Icons.Checkmark size={14} />
              </IconBadge>
              <div>
                <Text strong type="success" className={styles.captionText}>
                  Assessment complete
                </Text>
                <Text type="secondary" className={styles.captionText}>
                  {statusLabel}
                </Text>
              </div>
            </Flex>
          ) : (
            <>
              <Flex justify="space-between">
                <Text type="secondary" size="sm">
                  Completeness
                </Text>
                <Text strong size="sm">
                  {completeness}%
                </Text>
              </Flex>
              <Progress percent={completeness} showInfo={false} size="small" />
              <Flex justify="space-between" align="center" className="mt-1">
                <Text type={getStatusTextType(status)} size="sm">
                  {statusLabel}
                </Text>
                <Button type="link" style={{ padding: 0 }} onClick={onClick}>
                  Resume
                </Button>
              </Flex>
            </>
          )}
        </div>
      </Flex>
    </Card>
  );
};
