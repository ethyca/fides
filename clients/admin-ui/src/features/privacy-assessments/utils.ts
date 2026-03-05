import { FIELD_NAME_LABELS, SOURCE_TYPE_LABELS } from "./constants";
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

export const filterEvidence = (
  items: EvidenceItem[],
  query: string,
): EvidenceItem[] => {
  if (!query.trim()) {
    return items;
  }
  const lower = query.toLowerCase();
  return items.filter(
    (item) =>
      item.value.toLowerCase().includes(lower) ||
      (SOURCE_TYPE_LABELS[item.source_type] ?? item.source_type)
        .toLowerCase()
        .includes(lower) ||
      (FIELD_NAME_LABELS[item.field_name] ?? item.field_name.replace(/_/g, " "))
        .toLowerCase()
        .includes(lower),
  );
};
