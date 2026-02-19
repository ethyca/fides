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
import {
  AnswerSource,
  AnswerStatus,
  AssessmentQuestion,
  QuestionGroup,
} from "./types";
import { getTimeSince } from "./utils";

interface QuestionGroupPanelProps {
  group: QuestionGroup;
  isExpanded: boolean;
  getAnswerValue: (questionId: string, apiAnswer: string) => string;
  onAnswerChange: (questionId: string, value: string) => void;
  onAnswerSave: (questionId: string, value: string) => void;
  onComment: (selection: { text: string; start: number; end: number }) => void;
  onRequestInput: () => void;
  onViewEvidence: (groupId: string) => void;
}

export const buildQuestionGroupPanelItem = ({
  group,
  isExpanded,
  getAnswerValue,
  onAnswerChange,
  onAnswerSave,
  onComment,
  onRequestInput,
  onViewEvidence,
}: QuestionGroupPanelProps): NonNullable<CollapseProps["items"]>[number] => {
  const answeredCount = group.questions.filter((q) => {
    const answer = getAnswerValue(q.question_id, q.answer_text);
    return answer.trim().length > 0;
  }).length;
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
                    {group.last_updated_by
                      .split(" ")
                      .map((n: string) => n[0])
                      .join("")}
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
                onClick={(e) => {
                  e.stopPropagation();
                  onViewEvidence(group.id);
                }}
                size="small"
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
      {group.questions.map((q: AssessmentQuestion) => {
        const currentAnswer = getAnswerValue(q.question_id, q.answer_text);
        const needsInput =
          q.answer_source === AnswerSource.SLACK ||
          q.answer_status === AnswerStatus.NEEDS_INPUT;

        return (
          <QuestionCard
            key={q.id}
            question={q}
            currentAnswer={currentAnswer}
            onAnswerChange={onAnswerChange}
            onAnswerSave={onAnswerSave}
            onComment={onComment}
            onRequestInput={needsInput ? onRequestInput : undefined}
            onViewEvidence={() => onViewEvidence(group.id)}
          />
        );
      })}
    </Space>
  );

  return { key: group.id, label, children };
};
