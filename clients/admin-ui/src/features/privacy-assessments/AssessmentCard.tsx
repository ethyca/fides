import classNames from "classnames";
import {
  Avatar,
  Button,
  Card,
  CUSTOM_TAG_COLOR,
  Divider,
  Flex,
  Icons,
  Paragraph,
  Progress,
  Tag,
  TagList,
  Text,
  Typography,
} from "fidesui";
import NextLink from "next/link";

import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import { formatDate } from "~/features/common/utils";

import styles from "./AssessmentCard.module.scss";
import {
  ASSESSMENT_STATUS_LABELS,
  RISK_LEVEL_LABELS,
  RISK_TAG_COLORS,
} from "./constants";
import { AssessmentStatus, PrivacyAssessmentResponse } from "./types";

const { Title } = Typography;

type TextType = React.ComponentProps<typeof Typography.Text>["type"];

function getStatusTextType(status: AssessmentStatus): TextType {
  if (status === AssessmentStatus.COMPLETED) {
    return "success";
  }
  if (status === AssessmentStatus.OUTDATED) {
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
  const completionDate =
    isComplete && assessment.updated_at
      ? `Completed on ${formatDate(assessment.updated_at, { showTime: false })}`
      : statusLabel;

  return (
    <Card
      className={classNames(styles.cardWrapper, {
        [styles.cardComplete]: isComplete,
      })}
    >
      <Flex vertical gap="small" justify="space-between" className="flex-1">
        <div>
          <Title level={3} className={`!mb-1 ${styles.titleLink}`}>
            <NextLink href={`${PRIVACY_ASSESSMENTS_ROUTE}/${assessment.id}`}>
              {assessment.template_name ?? assessment.name}
            </NextLink>
          </Title>
          {assessment.system_name && (
            <div>
              <Text type="secondary" size="sm">
                {assessment.system_name}
              </Text>
            </div>
          )}
          <div className={styles.textWithTags}>
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
            )}
          </div>
          {riskLevel && (
            <div>
              <Tag
                color={RISK_TAG_COLORS[riskLevel] ?? CUSTOM_TAG_COLOR.DEFAULT}
              >
                {`${riskLabel} risk`}
              </Tag>
            </div>
          )}
        </div>
        <div>
          <Divider className="my-3" />
          <div>
            {isComplete ? (
              <Flex
                justify="space-between"
                align="center"
                className={styles.completeContainer}
              >
                <Flex align="center" gap="medium">
                  <Avatar
                    shape="circle"
                    size={28}
                    icon={<Icons.Checkmark size={14} />}
                    style={{ backgroundColor: "var(--fidesui-success)" }}
                  />
                  <div>
                    <Text strong type="success" size="sm">
                      Assessment complete
                    </Text>
                    <Paragraph type="secondary" size="sm">
                      {completionDate}
                    </Paragraph>
                  </div>
                </Flex>
                <Button type="link" className="p-0" onClick={onClick}>
                  View
                </Button>
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
                <Progress
                  percent={completeness}
                  showInfo={false}
                  size="small"
                />
                <Flex justify="space-between" align="center" className="mt-1">
                  <Text type={getStatusTextType(status)} size="sm">
                    {statusLabel}
                  </Text>
                  <Button type="link" className="p-0" onClick={onClick}>
                    Resume
                  </Button>
                </Flex>
              </>
            )}
          </div>
        </div>
      </Flex>
    </Card>
  );
};
