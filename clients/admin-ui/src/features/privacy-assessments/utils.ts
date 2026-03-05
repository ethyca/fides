import type { AssessmentQuestion, EvidenceItem } from "./types";
import { AnswerStatus } from "./types";

export const getSlackQuestions = (
  questions: AssessmentQuestion[],
): {
  slackQuestions: AssessmentQuestion[];
  answeredSlackQuestions: AssessmentQuestion[];
} => {
  const slackQuestions = questions.filter(
    (q) => q.answer_status === AnswerStatus.NEEDS_INPUT,
  );
  const answeredSlackQuestions = slackQuestions.filter(
    (q) => q.answer_text.trim().length > 0,
  );
  return { slackQuestions, answeredSlackQuestions };
};

export const deduplicateEvidence = (items: EvidenceItem[]): EvidenceItem[] => {
  const seen = new Set<string>();
  return items.filter((item) => {
    const key = `${item.source_type}|${item.source_key}|${item.field_name}|${item.value}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
};
