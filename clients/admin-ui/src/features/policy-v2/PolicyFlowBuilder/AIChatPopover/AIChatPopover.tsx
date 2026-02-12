import React, { useState } from "react";

import { PolicyV2Create } from "../../types";
import { AIChatPane } from "../AIChatPane";
import styles from "./AIChatPopover.module.scss";

interface AIChatPopoverProps {
  onPolicyGenerated: (policy: PolicyV2Create) => void;
  onPolicySave: (policy: PolicyV2Create) => void;
  aiPolicy: PolicyV2Create | null;
  hasExistingPolicy?: boolean;
  isUpdatingFlow?: boolean;
  isRevealing?: boolean;
  revealProgress?: number;
}

export const AIChatPopover = ({
  onPolicyGenerated,
  onPolicySave,
  aiPolicy,
  hasExistingPolicy,
  isUpdatingFlow,
  isRevealing,
  revealProgress = 0,
}: AIChatPopoverProps) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className={styles.popoverAnchor}>
      {/* Floating chat panel */}
      {isOpen && (
        <div className={styles.popoverPanel}>
          <div className={styles.popoverHeader}>
            <div className={styles.headerLeft}>
              <span className={styles.aiIndicator}>AI</span>
              <span className={styles.headerTitle}>AI Policy Builder</span>
            </div>
            <button
              type="button"
              className={styles.closeButton}
              onClick={() => setIsOpen(false)}
              aria-label="Collapse AI Chat"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path
                  d="M10.5 3.5L3.5 10.5M3.5 3.5L10.5 10.5"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                />
              </svg>
            </button>
          </div>

          {/* Progress indicator */}
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

          <div className={styles.popoverBody}>
            <AIChatPane
              onPolicyGenerated={onPolicyGenerated}
              onPolicySave={onPolicySave}
              generatedPolicy={aiPolicy}
              hasExistingPolicy={hasExistingPolicy}
            />
          </div>
        </div>
      )}

      {/* Toggle button */}
      <button
        type="button"
        className={`${styles.toggleButton} ${isOpen ? styles.open : ""}`}
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label={isOpen ? "Collapse AI Chat" : "Expand AI Chat"}
      >
        <span className={styles.toggleIcon}>AI</span>
        {!isOpen && <span className={styles.toggleLabel}>AI Chat</span>}
        {!isOpen && (
          <svg
            className={styles.chevron}
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="none"
          >
            <path
              d="M3 7.5L6 4.5L9 7.5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        )}
      </button>
    </div>
  );
};
