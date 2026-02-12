import React from "react";

import { NodePalette } from "../NodePalette";
import styles from "./SidePanel.module.scss";

interface SidePanelProps {
  onAddRule: () => void;
}

export const SidePanel = ({ onAddRule }: SidePanelProps) => {
  return (
    <div className={styles.sidePanel}>
      <div className={styles.panelHeader}>
        <span className={styles.headerIcon}>+</span>
        Nodes
      </div>
      <div className={styles.panelContent}>
        <NodePalette onAddRule={onAddRule} />
      </div>
    </div>
  );
};
