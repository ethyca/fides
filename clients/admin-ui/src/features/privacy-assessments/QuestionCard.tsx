import { CUSTOM_TAG_COLOR, Flex, Tag, Text, Tooltip } from "fidesui";

import { ANSWER_SOURCE_LABELS, ANSWER_SOURCE_TAG_COLORS } from "./constants";
import { EditableTextBlock } from "./EditableTextBlock";
import styles from "./QuestionCard.module.scss";
import { ReferenceBadge } from "./ReferenceBadge";
import { AnswerStatus, AssessmentQuestion } from "./types";

interface QuestionCardProps {
  question: AssessmentQuestion;
  currentAnswer: string;
  onAnswerChange: (questionId: string, value: string) => void;
  onAnswerSave: (questionId: string, value: string) => void;
  onComment: (selection: { text: string; start: number; end: number }) => void;
  onRequestInput?: () => void;
  onViewEvidence: () => void;
}

export const QuestionCard = ({
  question,
  currentAnswer,
  onAnswerChange,
  onAnswerSave,
  onComment,
  onRequestInput,
  onViewEvidence,
}: QuestionCardProps) => {
  const sourceLabel = ANSWER_SOURCE_LABELS[question.answer_source];
  const sourceColor = ANSWER_SOURCE_TAG_COLORS[question.answer_source];

  return (
    <div className={styles.container}>
      <Flex justify="space-between" align="center" className={styles.header}>
        <Text strong>
          {question.id}. {question.question_text}
        </Text>
        {question.answer_status === AnswerStatus.PARTIAL ? (
          <Tooltip
            title={
              question.missing_data && question.missing_data.length > 0
                ? `This answer can be automatically derived if you populate: ${question.missing_data.join(", ")}`
                : "This answer can be derived from Fides data if the relevant field is populated"
            }
          >
            <Tag color={CUSTOM_TAG_COLOR.WARNING}>System derivable</Tag>
          </Tooltip>
        ) : (
          <Tag color={sourceColor}>{sourceLabel}</Tag>
        )}
      </Flex>
      <EditableTextBlock
        value={currentAnswer}
        onChange={(newValue) => onAnswerChange(question.question_id, newValue)}
        onSave={(newValue) => onAnswerSave(question.question_id, newValue)}
        placeholder="Enter your answer..."
        onComment={onComment}
        onRequestInput={onRequestInput}
        renderContent={(text) => (
          <ReferenceBadge
            text={text}
            onReferenceClick={() => onViewEvidence()}
          />
        )}
      />
    </div>
  );
};
