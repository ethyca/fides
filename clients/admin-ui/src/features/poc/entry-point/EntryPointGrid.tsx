import { LayoutGroup, motion } from "framer-motion";
import { useState } from "react";

import { ActivityFeedCard } from "./ActivityFeedCard";
import { AiAgentActivityCard } from "./AiAgentActivityCard";
import AiBriefingCard from "./AiBriefingCard";
import { BusinessUnitsCard } from "./BusinessUnitsCard";
import { DsrStatusCard } from "./DsrStatusCard";
import { GenerateReportCard } from "./GenerateReportCard";
import { getCardStyle } from "./gridLayout";
import HealthScoreCard from "./HealthScoreCard";
import { PriorityActionsCard } from "./PriorityActionsCard";
import { PrivacyAssessmentsCard } from "./PrivacyAssessmentsCard";
import { RisksCard } from "./RisksCard";
import { SystemCoverageCard } from "./SystemCoverageCard";
import TrendCard from "./TrendCard";
import { CardId, CardProps } from "./types";

const ALL_CARDS: CardId[] = [
  "health-score",
  "ai-briefing",
  "trend-governance-posture",
  "trend-dsr-volume",
  "trend-system-coverage",
  "trend-classification-health",
  "priority-actions",
  "risks",
  "privacy-assessments",
  "business-units",
  "system-coverage",
  "activity-feed",
  "ai-agent-activity",
  "dsr-status",
  "generate-report",
];

const SURFACE_CARDS: CardId[] = ["health-score", "ai-briefing"];

const noop = () => {};

const renderCard = (cardId: CardId, props: CardProps) => {
  switch (cardId) {
    case "health-score":
      return <HealthScoreCard {...props} />;
    case "ai-briefing":
      return <AiBriefingCard {...props} />;
    case "trend-governance-posture":
      return <TrendCard metric="governance-posture" {...props} />;
    case "trend-dsr-volume":
      return <TrendCard metric="dsr-volume" {...props} />;
    case "trend-system-coverage":
      return <TrendCard metric="system-coverage" {...props} />;
    case "trend-classification-health":
      return <TrendCard metric="classification-health" {...props} />;
    case "priority-actions":
      return <PriorityActionsCard {...props} />;
    case "risks":
      return <RisksCard {...props} />;
    case "privacy-assessments":
      return <PrivacyAssessmentsCard {...props} />;
    case "business-units":
      return <BusinessUnitsCard {...props} />;
    case "system-coverage":
      return <SystemCoverageCard {...props} />;
    case "activity-feed":
      return <ActivityFeedCard {...props} />;
    case "ai-agent-activity":
      return <AiAgentActivityCard {...props} />;
    case "dsr-status":
      return <DsrStatusCard {...props} />;
    case "generate-report":
      return <GenerateReportCard {...props} />;
    default:
      return null;
  }
};

const EntryPointGrid = () => {
  const [expandedCard, setExpandedCard] = useState<CardId>("priority-actions");

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(12, 1fr)",
        gridTemplateRows: "repeat(8, 1fr)",
        width: "100vw",
        height: "100vh",
        gap: "8px",
        padding: "8px",
        boxSizing: "border-box",
        background: "#f5f5f5",
      }}
    >
      <LayoutGroup>
        {ALL_CARDS.map((cardId) => {
          const isSurface = SURFACE_CARDS.includes(cardId);
          const state = cardId === expandedCard ? "expanded" : "compressed";
          return (
            <motion.div
              key={cardId}
              layout
              layoutId={cardId}
              style={{
                ...getCardStyle(cardId, expandedCard),
                border: isSurface ? "none" : "1px solid #ccc",
                background: isSurface ? "transparent" : "white",
                overflow: "hidden",
                cursor: "pointer",
              }}
              transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
              onClick={() => setExpandedCard(cardId)}
            >
              {renderCard(cardId, { state, onClick: noop })}
            </motion.div>
          );
        })}
      </LayoutGroup>
    </div>
  );
};

export default EntryPointGrid;
