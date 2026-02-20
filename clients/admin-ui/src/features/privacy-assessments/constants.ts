import { CUSTOM_TAG_COLOR } from "fidesui";

import { AssessmentStatus, RiskLevel } from "./types";

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
