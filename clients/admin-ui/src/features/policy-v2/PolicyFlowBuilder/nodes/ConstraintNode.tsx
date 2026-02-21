import React, { memo } from "react";
import { Handle, Position, NodeProps, Node } from "@xyflow/react";
import { ConstraintNodeData } from "../types";
import {
  PrivacyConstraintConfig,
  ContextConstraintConfig,
  DataFlowConstraintConfig,
} from "../../types";
import styles from "./nodeStyles.module.scss";

export type ConstraintNodeType = Node<ConstraintNodeData, "constraint">;

const ConstraintNode = ({ data, selected }: NodeProps<ConstraintNodeType>) => {
  const { constraint } = data;
  const isPrivacy = constraint.constraint_type === "privacy";
  const isDataFlow = constraint.constraint_type === "data_flow";

  const getIconClass = () => {
    if (isPrivacy) return styles.constraintIconPrivacy;
    if (isDataFlow) return styles.constraintIconDataFlow;
    return styles.constraintIconContext;
  };

  const getTitle = () => {
    if (isPrivacy) return "Privacy Constraint";
    if (isDataFlow) return "Data Flow Constraint";
    return "Context Constraint";
  };

  const renderDetails = () => {
    if (isPrivacy) {
      const config = constraint.configuration as PrivacyConstraintConfig;
      return (
        <>
          <div className={styles.nodeDetailRow}>
            <span className={styles.nodeDetailKey}>Notice:</span>
            <span className={`${styles.nodeDetailValue} ${styles.textMono}`}>
              {config.privacy_notice_key || "—"}
            </span>
          </div>
          <span className={styles.constraintBadge}>
            {config.requirement === "opt_in" ? "Requires Opt-In" : "Not Opted Out"}
          </span>
        </>
      );
    }

    if (isDataFlow) {
      const config = constraint.configuration as DataFlowConstraintConfig;
      const directionLabel = config.direction === "ingress" ? "Source" : "Destination";
      const operatorLabel = config.operator === "any_of" ? "Any Of" : "None Of";
      const systemsText = config.systems.slice(0, 2).join(", ");
      const hasMore = config.systems.length > 2;

      return (
        <>
          <div className={styles.nodeDetailRow}>
            <span className={styles.nodeDetailKey}>Direction:</span>
            <span className={styles.nodeDetailValue}>{directionLabel}</span>
          </div>
          <div className={styles.nodeDetailRow}>
            <span className={styles.nodeDetailKey}>{operatorLabel}:</span>
            <span className={`${styles.nodeDetailValue} ${styles.textMono}`}>
              {systemsText || "—"}{hasMore && ` +${config.systems.length - 2}`}
            </span>
          </div>
        </>
      );
    }

    const config = constraint.configuration as ContextConstraintConfig;
    const valueText = config.values.slice(0, 2).join(", ");
    const hasMore = config.values.length > 2;

    return (
      <>
        <div className={styles.nodeDetailRow}>
          <span className={styles.nodeDetailKey}>Field:</span>
          <span className={`${styles.nodeDetailValue} ${styles.textMono}`}>
            {config.field || "—"}
          </span>
        </div>
        <div className={styles.nodeDetailRow}>
          <span className={styles.nodeDetailKey}>{config.operator}:</span>
          <span className={styles.nodeDetailValue}>
            {valueText}{hasMore && ` +${config.values.length - 2}`}
          </span>
        </div>
      </>
    );
  };

  return (
    <div
      className={`${styles.constraintNode} ${selected ? styles.selected : ""}`}
      data-testid="constraint-node"
    >
      <Handle
        type="target"
        position={Position.Left}
        className={`${styles.handle} ${styles.handleTarget}`}
      />

      <div className={styles.nodeInner}>
        <div
          className={`${styles.constraintIcon} ${getIconClass()}`}
        />
        <div className={styles.nodeBody}>
          <p className={styles.nodeTitle}>{getTitle()}</p>
          <div className={styles.nodeDetails}>{renderDetails()}</div>
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Right}
        className={`${styles.handle} ${styles.handleSource}`}
      />
    </div>
  );
};

ConstraintNode.displayName = "ConstraintNode";

export default memo(ConstraintNode);
