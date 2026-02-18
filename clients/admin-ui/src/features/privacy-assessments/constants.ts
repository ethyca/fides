import { CUSTOM_TAG_COLOR } from "fidesui";

import { AssessmentStatus, RiskLevel } from "./types";

export const ASSESSMENT_STATUS_LABELS: Record<string, string> = {
  in_progress: "In progress",
  completed: "Completed",
  outdated: "Out of date",
} satisfies Record<AssessmentStatus, string>;

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
