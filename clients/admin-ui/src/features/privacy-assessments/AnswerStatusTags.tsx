import { Tag, Tooltip } from "fidesui";

import {
  ANSWER_SOURCE_LABELS,
  ANSWER_SOURCE_TAG_COLORS,
  ANSWER_STATUS_LABELS,
  ANSWER_STATUS_TAG_COLORS,
} from "./constants";
import { AnswerStatus, AssessmentQuestion } from "./types";

interface AnswerStatusTagsProps {
  question: AssessmentQuestion;
}

export const AnswerStatusTags = ({ question }: AnswerStatusTagsProps) => {
  if (question.answer_status === AnswerStatus.COMPLETE) {
    return (
      <Tag color={ANSWER_SOURCE_TAG_COLORS[question.answer_source]}>
        {ANSWER_SOURCE_LABELS[question.answer_source]}
      </Tag>
    );
  }

  const statusTag = (
    <Tag color={ANSWER_STATUS_TAG_COLORS[question.answer_status]}>
      {ANSWER_STATUS_LABELS[question.answer_status]}
    </Tag>
  );

  if (question.answer_status === AnswerStatus.PARTIAL) {
    const tooltipTitle =
      question.missing_data && question.missing_data.length > 0
        ? `This answer can be automatically derived if you populate: ${question.missing_data.join(", ")}`
        : "This answer can be derived from Fides data if the relevant field is populated";

    return <Tooltip title={tooltipTitle}>{statusTag}</Tooltip>;
  }

  return statusTag;
};
