import { CUSTOM_TAG_COLOR } from "fidesui";

import { AnswerSource, AssessmentStatus, RiskLevel } from "./types";

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
  [AnswerSource.AI_ANALYSIS]: "AI derived",
  [AnswerSource.USER_INPUT]: "Team input",
  [AnswerSource.SLACK]: "Team input",
};

export const ANSWER_SOURCE_TAG_COLORS: Record<AnswerSource, CUSTOM_TAG_COLOR> =
  {
    [AnswerSource.SYSTEM]: CUSTOM_TAG_COLOR.SUCCESS,
    [AnswerSource.AI_ANALYSIS]: CUSTOM_TAG_COLOR.SUCCESS,
    [AnswerSource.USER_INPUT]: CUSTOM_TAG_COLOR.DEFAULT,
    [AnswerSource.SLACK]: CUSTOM_TAG_COLOR.DEFAULT,
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
