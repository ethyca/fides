import { Flex, Space, Text, useMessage } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";
import { RTKErrorResult } from "~/types/errors/api";

import { AnswerStatusTags } from "./AnswerStatusTags";
import { EditableTextBlock } from "./EditableTextBlock";
import { useUpdateAssessmentAnswerMutation } from "./privacy-assessments.slice";
import styles from "./QuestionCard.module.scss";
import { AssessmentQuestion } from "./types";

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
        <Space size="small">
          <AnswerStatusTags question={question} />
        </Space>
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
