/**
 * Privacy Assessments Constants
 *
 * Centralized constants and label mappings for privacy assessments.
 */

import { AssessmentStatus, RiskLevel } from "./types";

// =============================================================================
// Status Labels
// =============================================================================

export const ASSESSMENT_STATUS_LABELS: Record<AssessmentStatus, string> = {
  in_progress: "In progress",
  completed: "Completed",
  outdated: "Out of date",
};

// =============================================================================
// Risk Level Labels
// =============================================================================

export const RISK_LEVEL_LABELS: Record<RiskLevel, string> = {
  high: "High",
  medium: "Med",
  low: "Low",
};
