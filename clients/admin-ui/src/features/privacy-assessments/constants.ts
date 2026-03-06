import { CUSTOM_TAG_COLOR } from "fidesui";

import {
  AnswerSource,
  AnswerStatus,
  AssessmentStatus,
  RiskLevel,
} from "./types";

export const ASSESSMENT_STATUS_LABELS: Record<AssessmentStatus, string> = {
  [AssessmentStatus.IN_PROGRESS]: "In progress",
  [AssessmentStatus.COMPLETED]: "Completed",
  [AssessmentStatus.OUTDATED]: "Out of date",
};

export const RISK_LEVEL_LABELS: Record<RiskLevel, string> = {
  [RiskLevel.HIGH]: "High",
  [RiskLevel.MEDIUM]: "Med",
  [RiskLevel.LOW]: "Low",
};

export const RISK_TAG_COLORS: Record<RiskLevel, CUSTOM_TAG_COLOR> = {
  [RiskLevel.HIGH]: CUSTOM_TAG_COLOR.ERROR,
  [RiskLevel.MEDIUM]: CUSTOM_TAG_COLOR.WARNING,
  [RiskLevel.LOW]: CUSTOM_TAG_COLOR.DEFAULT,
};

export const ANSWER_SOURCE_LABELS: Record<AnswerSource, string> = {
  [AnswerSource.SYSTEM]: "System derived",
  [AnswerSource.AI_ANALYSIS]: "Agent",
  [AnswerSource.USER_INPUT]: "Manual input",
  [AnswerSource.TEAM_INPUT]: "Via Slack",
};

export const ANSWER_STATUS_LABELS: Record<AnswerStatus, string> = {
  [AnswerStatus.COMPLETE]: "Complete",
  [AnswerStatus.PARTIAL]: "System derivable",
  [AnswerStatus.NEEDS_INPUT]: "Needs input",
};

export const ANSWER_STATUS_TAG_COLORS: Record<AnswerStatus, CUSTOM_TAG_COLOR> =
  {
    [AnswerStatus.COMPLETE]: CUSTOM_TAG_COLOR.SUCCESS,
    [AnswerStatus.PARTIAL]: CUSTOM_TAG_COLOR.WARNING,
    [AnswerStatus.NEEDS_INPUT]: CUSTOM_TAG_COLOR.WARNING,
  };

export const RISK_LEVEL_DOT_COLORS: Record<RiskLevel, string> = {
  [RiskLevel.HIGH]: "var(--fidesui-error)",
  [RiskLevel.MEDIUM]: "var(--fidesui-warning)",
  [RiskLevel.LOW]: "var(--fidesui-success)",
};

export const FREQUENCY_OPTIONS = [
  { label: "Daily", value: "daily", cron: "0 9 * * *" },
  { label: "Weekly (Mondays)", value: "weekly", cron: "0 9 * * 1" },
  { label: "Monthly (1st)", value: "monthly", cron: "0 9 1 * *" },
  { label: "Yearly (Jan 1st)", value: "yearly", cron: "0 9 1 1 *" },
];

export const SOURCE_TYPE_LABELS: Record<string, string> = {
  system: "System",
  privacy_declaration: "Data uses",
  data_category: "Data category",
  data_use: "Data use",
  data_subject: "Data subject",
  dataset: "Dataset",
  data_flow: "Data flow",
  connection: "Connection",
};

export const FIELD_NAME_LABELS: Record<string, string> = {
  name: "Name",
  description: "Description",
  data_use: "Data use",
  data_categories: "Data categories",
  data_subjects: "Data subjects",
  retention_period: "Retention period",
  third_parties: "Third parties",
};
