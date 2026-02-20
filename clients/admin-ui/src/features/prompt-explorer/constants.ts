import type { DataSectionConfig } from "./types";

/**
 * Default configuration for data sections - all enabled by default.
 */
export const DEFAULT_DATA_SECTIONS: DataSectionConfig = {
  organization: true,
  data_categories: true,
  data_uses: true,
  data_subjects: true,
  systems: true,
  datasets: true,
  policies: true,
  privacy_notices: true,
  connections: true,
};

/**
 * Intent classification action types for questionnaire prompts.
 */
export const ACTION_TYPES: Array<{ value: string; label: string }> = [
  { value: "answer", label: "Answer" },
  { value: "skip", label: "Skip" },
  { value: "correct", label: "Correct Previous" },
  { value: "wait", label: "Wait" },
  { value: "clarify_question", label: "Clarify Question" },
  { value: "request_clarification", label: "Request Clarification" },
  { value: "acknowledge", label: "Acknowledge" },
  { value: "restart_all", label: "Restart All" },
  { value: "restart_from", label: "Restart From" },
  { value: "summary", label: "Summary" },
];
