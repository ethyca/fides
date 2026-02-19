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

import useTaxonomies from "~/features/common/hooks/useTaxonomies";

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
        <Text type="secondary" size="sm">
          System: {assessment.system_name ?? ""}
        </Text>
        <Text type="secondary" size="sm" className={styles.textWithTags}>
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

        <Divider className="my-3" />
        <div>
          {isComplete ? (
            <Flex
              align="center"
              gap="middle"
              className={styles.completeContainer}
            >
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
                  {statusLabel}
                </Paragraph>
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
                <Button type="link" className="p-0" onClick={onClick}>
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
