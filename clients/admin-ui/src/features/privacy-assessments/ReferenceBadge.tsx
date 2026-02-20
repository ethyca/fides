import React from "react";

import styles from "./ReferenceBadge.module.scss";

interface ReferenceBadgeProps {
  text: string;
  onReferenceClick?: (label: string) => void;
}

export const ReferenceBadge = ({
  text,
  onReferenceClick,
}: ReferenceBadgeProps) => {
  const referencePattern = /\[([^\]]+)\]/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match = referencePattern.exec(text);
  let refIndex = 0;

  while (match !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }
    const label = match[1];
    const currentRefIndex = refIndex;
    refIndex += 1;
    parts.push(
      <span
        key={`ref-${currentRefIndex}`}
        role="button"
        tabIndex={0}
        className={styles.reference}
        onClick={(e) => {
          e.stopPropagation();
          onReferenceClick?.(label);
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.stopPropagation();
            onReferenceClick?.(label);
          }
        }}
      >
        {label}
      </span>,
    );
    lastIndex = match.index + match[0].length;
    match = referencePattern.exec(text);
  }
  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  // eslint-disable-next-line react/jsx-no-useless-fragment
  return <>{parts}</>;
};
