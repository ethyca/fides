import {
  CUSTOM_TAG_COLOR,
  Flex,
  Tag,
  Text,
  Tooltip,
  useMessage,
} from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";
import { RTKErrorResult } from "~/types/errors/api";

import { ANSWER_SOURCE_LABELS, ANSWER_SOURCE_TAG_COLORS } from "./constants";
import { EditableTextBlock } from "./EditableTextBlock";
import { useUpdateAssessmentAnswerMutation } from "./privacy-assessments.slice";
import styles from "./QuestionCard.module.scss";
import { AnswerStatus, AssessmentQuestion } from "./types";

interface QuestionCardProps {
  assessmentId: string;
  question: AssessmentQuestion;
}

export const QuestionCard = ({ assessmentId, question }: QuestionCardProps) => {
  const message = useMessage();
  const [updateAnswer, { isLoading: isSaving }] =
    useUpdateAssessmentAnswerMutation();

  const sourceLabel = ANSWER_SOURCE_LABELS[question.answer_source];
  const sourceColor = ANSWER_SOURCE_TAG_COLORS[question.answer_source];

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
        value={question.answer_text}
        onSave={handleSave}
        isLoading={isSaving}
        placeholder="Enter your answer..."
      />
    </div>
  );
};
