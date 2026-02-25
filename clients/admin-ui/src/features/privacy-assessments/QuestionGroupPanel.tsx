import type { CollapseProps } from "antd";
import {
  Badge,
  Button,
  CUSTOM_TAG_COLOR,
  Flex,
  Icons,
  Space,
  Tag,
  Text,
} from "fidesui";

import { RISK_LEVEL_DOT_COLORS, RISK_LEVEL_LABELS } from "./constants";
import { QuestionCard } from "./QuestionCard";
import styles from "./QuestionGroupPanel.module.scss";
import { QuestionGroup } from "./types";
import { getInitials, getTimeSince } from "./utils";

interface QuestionGroupPanelProps {
  assessmentId: string;
  group: QuestionGroup;
  isExpanded: boolean;
}

export const buildQuestionGroupPanelItem = ({
  assessmentId,
  group,
  isExpanded,
}: QuestionGroupPanelProps): NonNullable<CollapseProps["items"]>[number] => {
  const answeredCount = group.questions.filter(
    (q) => q.answer_text.trim().length > 0,
  ).length;
  const totalCount = group.questions.length;
  const isGroupCompleted = answeredCount === totalCount;

  const label = (
    <>
      <Flex gap="large" align="flex-start" className={styles.labelFlex}>
        <div className={styles.labelContent}>
          <Text strong className={styles.groupTitle}>
            {group.id}. {group.title}
          </Text>
          <Flex gap="middle" align="center" wrap="wrap" className={styles.meta}>
            <Text type="secondary" size="sm">
              {group.last_updated_at
                ? `Updated ${getTimeSince(group.last_updated_at)}`
                : "Not updated yet"}
              {group.last_updated_by && (
                <>
                  {" by "}
                  <Tag
                    color={CUSTOM_TAG_COLOR.DEFAULT}
                    className={styles.avatarTag}
                  >
                    {getInitials(group.last_updated_by)}
                  </Tag>
                </>
              )}
            </Text>
            <Text type="secondary" size="sm">
              <Text strong size="sm">
                Fields:
              </Text>{" "}
              {answeredCount}/{totalCount}
            </Text>
            {group.risk_level && (
              <Flex gap="small" align="center">
                <Badge color={RISK_LEVEL_DOT_COLORS[group.risk_level]} />
                <Text size="sm">
                  Risk: {RISK_LEVEL_LABELS[group.risk_level]}
                </Text>
              </Flex>
            )}
          </Flex>
          {isExpanded && (
            <Flex align="center" gap="small" className={styles.evidenceButton}>
              <Button
                type="default"
                icon={<Icons.Document />}
                size="small"
                disabled
              >
                View evidence
              </Button>
            </Flex>
          )}
        </div>
      </Flex>
      <div className={styles.statusTag}>
        <Tag
          color={
            isGroupCompleted
              ? CUSTOM_TAG_COLOR.SUCCESS
              : CUSTOM_TAG_COLOR.DEFAULT
          }
        >
          {isGroupCompleted ? "Completed" : "Pending"}
        </Tag>
      </div>
    </>
  );

  const children = (
    <Space direction="vertical" size="middle" className={styles.questions}>
      {group.questions.map((q) => (
        <QuestionCard key={q.id} assessmentId={assessmentId} question={q} />
      ))}
    </Space>
  );

  return { key: group.id, label, children };
};
