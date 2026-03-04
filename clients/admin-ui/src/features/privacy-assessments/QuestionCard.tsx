import { Flex, Tag, Text, useMessage } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";
import { RTKErrorResult } from "~/types/errors/api";

import {
  ANSWER_SOURCE_LABELS,
  ANSWER_SOURCE_TAG_COLORS,
  ANSWER_STATUS_LABELS,
  ANSWER_STATUS_TAG_COLORS,
} from "./constants";
import { EditableTextBlock } from "./EditableTextBlock";
import { useUpdateAssessmentAnswerMutation } from "./privacy-assessments.slice";
import styles from "./QuestionCard.module.scss";
import { AnswerStatus, AnswerSource, AssessmentQuestion } from "./types";

interface QuestionCardProps {
  assessmentId: string;
  question: AssessmentQuestion;
}

export const QuestionCard = ({ assessmentId, question }: QuestionCardProps) => {
  const message = useMessage();
  const [updateAnswer, { isLoading: isSaving }] =
    useUpdateAssessmentAnswerMutation();

  const handleSave = async (newAnswer: string) => {
    try {
      await updateAnswer({
        id: assessmentId,
        questionId: question.question_id,
        body: { answer_text: newAnswer },
      }).unwrap();
    } catch (error) {
      message.error(
        getErrorMessage(
          error as RTKErrorResult["error"],
          "Failed to save answer. Please try again.",
        ),
      );
    }
  };

  return (
    <div className={`${styles.container} p-4 pb-2`}>
      <Flex justify="space-between" align="center" className="mb-3">
        <Text strong>
          {question.id}. {question.question_text}
        </Text>
        {question.answer_status === AnswerStatus.COMPLETE ? (
          <Tag
            color={ANSWER_SOURCE_TAG_COLORS[question.answer_source]}
            hasSparkle={question.answer_source === AnswerSource.AI_ANALYSIS}
          >
            {ANSWER_SOURCE_LABELS[question.answer_source]}
          </Tag>
        ) : (
          <Tag color={ANSWER_STATUS_TAG_COLORS[question.answer_status]}>
            {ANSWER_STATUS_LABELS[question.answer_status]}
          </Tag>
        )}
      </Flex>
      <EditableTextBlock
        value={question.answer_text}
        onSave={handleSave}
        isLoading={isSaving}
        placeholder="Enter your answer..."
      />
    </div>
  );
};
