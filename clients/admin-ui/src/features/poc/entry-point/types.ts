export type CardId =
  | "health-score"
  | "ai-briefing"
  | "trend-governance-posture"
  | "trend-dsr-volume"
  | "trend-system-coverage"
  | "trend-classification-health"
  | "priority-actions"
  | "risks"
  | "privacy-assessments"
  | "business-units"
  | "system-coverage"
  | "activity-feed"
  | "ai-agent-activity"
  | "dsr-status"
  | "generate-report";

export type CardState = "compressed" | "expanded";

export interface CardProps {
  state: CardState;
  onClick: () => void;
}
