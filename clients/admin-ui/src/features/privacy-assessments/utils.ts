import type { AssessmentQuestion } from "./types";
import { AnswerSource, AnswerStatus } from "./types";

export const getInitials = (name: string): string =>
  name
    .split(" ")
    .map((n) => n[0])
    .join("");

export const getTimeSince = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffDays > 0) {
    return `${diffDays}d ago`;
  }
  if (diffHours > 0) {
    return `${diffHours}h ago`;
  }
  if (diffMins > 0) {
    return `${diffMins}m ago`;
  }
  return "Just now";
};

export const isAssessmentComplete = (
  questions: AssessmentQuestion[],
  getAnswerValue: (questionId: string, apiAnswer: string) => string,
): boolean =>
  questions.every(
    (q) => getAnswerValue(q.question_id, q.answer_text).trim().length > 0,
  );

export const getSlackQuestions = (
  questions: AssessmentQuestion[],
  getAnswerValue: (questionId: string, apiAnswer: string) => string,
): {
  slackQuestions: AssessmentQuestion[];
  answeredSlackQuestions: AssessmentQuestion[];
} => {
  const slackQuestions = questions.filter(
    (q) =>
      q.answer_source === AnswerSource.SLACK ||
      q.answer_status === AnswerStatus.NEEDS_INPUT,
  );
  const answeredSlackQuestions = slackQuestions.filter(
    (q) => getAnswerValue(q.question_id, q.answer_text).trim().length > 0,
  );
  return { slackQuestions, answeredSlackQuestions };
};
