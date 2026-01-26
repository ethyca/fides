import React, { memo } from "react";
import { Handle, Position, NodeProps, Node } from "@xyflow/react";
import { MatchNodeData } from "../types";
import { TaxonomyMatchValue } from "../../types";
import styles from "./nodeStyles.module.scss";

export type MatchNodeType = Node<MatchNodeData, "match">;

const MatchNode = ({ data, selected }: NodeProps<MatchNodeType>) => {
  const { match } = data;

  // Format and limit displayed values
  const formatValues = (values: (string | TaxonomyMatchValue)[]) => {
    return values.slice(0, 3).map((v, i) => {
      const text = typeof v === "string" ? v : `${v.taxonomy}.${v.element}`;
      // Truncate long values
      const truncated = text.length > 28 ? `${text.substring(0, 28)}…` : text;
      return (
        <span key={i} className={styles.matchValueTag}>
          {truncated}
        </span>
      );
    });
  };

  const remainingCount = match.values.length - 3;

  return (
    <div
      className={`${styles.matchNode} ${selected ? styles.selected : ""}`}
      data-testid="match-node"
    >
      <Handle
        type="target"
        position={Position.Left}
        className={`${styles.handle} ${styles.handleTarget}`}
      />

      <div className={styles.nodeInner}>
        <div className={styles.matchIcon} />
        <div className={styles.nodeBody}>
          <p className={styles.nodeTitle}>Match Condition</p>
          <p className={styles.nodeSubtitle}>
            {match.match_type === "key" ? "Key" : "Taxonomy"} → {match.target_field}
          </p>

          <div className={styles.nodeDetails}>
            <div className={styles.nodeDetailRow}>
              <span className={styles.nodeDetailKey}>Operator:</span>
              <span className={styles.nodeDetailValueBadge}>
                {match.operator === "any" ? "OR" : "AND"}
              </span>
            </div>
          </div>

          {match.values.length > 0 && (
            <div className={styles.matchValues}>
              {formatValues(match.values)}
              {remainingCount > 0 && (
                <span className={styles.matchValueMore}>+{remainingCount}</span>
              )}
            </div>
          )}
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

MatchNode.displayName = "MatchNode";

export default memo(MatchNode);
