import React from "react";

import { PolicyV2Create } from "../../types";
import { AIChatPane } from "../AIChatPane";
import { NodePalette } from "../NodePalette";
import styles from "./SidePanel.module.scss";

export type SidePanelMode = "nodes" | "chat";

interface SidePanelProps {
  mode: SidePanelMode;
  onModeChange: (mode: SidePanelMode) => void;
  onAddRule: () => void;
  onAIPolicyGenerated: (policy: PolicyV2Create) => void;
  onAIPolicySave: (policy: PolicyV2Create) => void;
  aiPolicy: PolicyV2Create | null;
  isUpdatingFlow?: boolean;
  isRevealing?: boolean;
  revealProgress?: number; // 0-100 percentage
  hasExistingPolicy?: boolean;
}

export const SidePanel = ({
  mode,
  onModeChange,
  onAddRule,
  onAIPolicyGenerated,
  onAIPolicySave,
  aiPolicy,
  isUpdatingFlow,
  isRevealing,
  revealProgress = 0,
  hasExistingPolicy,
}: SidePanelProps) => {
  return (
    <div className={styles.sidePanel}>
      <div className={styles.tabsHeader}>
        <button
          type="button"
          className={`${styles.tab} ${mode === "nodes" ? styles.active : ""}`}
          onClick={() => onModeChange("nodes")}
        >
          <span className={styles.tabIcon}>+</span>
          Nodes
        </button>
        <button
          type="button"
          className={`${styles.tab} ${mode === "chat" ? styles.active : ""}`}
          onClick={() => onModeChange("chat")}
        >
          <span className={styles.aiIndicator}>AI</span>
          AI Chat
        </button>
      </div>

      {isRevealing && (
        <div className={styles.buildingIndicator}>
          <div className={styles.buildingHeader}>
            <div className={styles.pulsingDot} />
            Building policy flow...
          </div>
          <div className={styles.progressBar}>
            <div
              className={styles.progressFill}
              style={{ width: `${revealProgress}%` }}
            />
          </div>
        </div>
      )}

      {isUpdatingFlow && !isRevealing && (
        <div className={styles.updatingIndicator}>
          <div className={styles.spinner} />
          Updating flow...
        </div>
      )}

      <div className={styles.tabContent}>
        {mode === "nodes" ? (
          <NodePalette onAddRule={onAddRule} />
        ) : (
          <AIChatPane
            onPolicyGenerated={onAIPolicyGenerated}
            onPolicySave={onAIPolicySave}
            generatedPolicy={aiPolicy}
            hasExistingPolicy={hasExistingPolicy}
          />
        )}
      </div>
    </div>
  );
};
