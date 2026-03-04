import type { AssessmentQuestion, AssessmentTaskResponse } from "./types";
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

export const formatSystems = (task: AssessmentTaskResponse | null): string => {
  if (!task) {
    return "—";
  }

  // Prefer systems array with name fallback to fides_key
  if (task.systems && task.systems.length > 0) {
    return task.systems
      .map((system) => system.name ?? system.fides_key)
      .join(", ");
  }

  // Fall back to system_fides_keys
  if (task.system_fides_keys && task.system_fides_keys.length > 0) {
    return task.system_fides_keys.join(", ");
  }

  return "All systems";
};

export const formatTypes = (
  assessmentTypes: string[],
  namesMap?: Record<string, string>,
): string => {
  if (assessmentTypes.length === 0) {
    return "—";
  }
  return assessmentTypes.map((t) => namesMap?.[t] ?? t).join(", ");
};
