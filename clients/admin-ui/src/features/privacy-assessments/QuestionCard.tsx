import { Flex, Tag, Text, Tooltip, useMessage } from "fidesui";

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
import { AnswerSource, AnswerStatus, AssessmentQuestion } from "./types";

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

  let statusTag;
  if (question.answer_status === AnswerStatus.COMPLETE) {
    statusTag = (
      <Tag
        color={ANSWER_SOURCE_TAG_COLORS[question.answer_source]}
        hasSparkle={question.answer_source === AnswerSource.AI_ANALYSIS}
      >
        {ANSWER_SOURCE_LABELS[question.answer_source]}
      </Tag>
    );
  } else if (question.answer_status === AnswerStatus.PARTIAL) {
    const tooltipTitle =
      question.missing_data?.length > 0
        ? `This answer can be automatically derived if you populate: ${question.missing_data.join(", ")}`
        : "This answer can be derived from Fides data if the relevant field is populated";
    statusTag = (
      <Tooltip title={tooltipTitle}>
        <Tag color={ANSWER_STATUS_TAG_COLORS[question.answer_status]}>
          {ANSWER_STATUS_LABELS[question.answer_status]}
        </Tag>
      </Tooltip>
    );
  } else {
    statusTag = (
      <Tag color={ANSWER_STATUS_TAG_COLORS[question.answer_status]}>
        {ANSWER_STATUS_LABELS[question.answer_status]}
      </Tag>
    );
  }

  return (
    <div className={`${styles.container} p-4 pb-2`}>
      <Flex justify="space-between" align="center" className="mb-3">
        <Text strong>
          {question.id}. {question.question_text}
        </Text>
        {statusTag}
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
