import { ExitGrid } from "fidesui";
import { HTMLAttributes, useMemo } from "react";

import { ConfidenceBucket } from "~/types/api/models/ConfidenceBucket";

import { ConfidenceCard } from "./ConfidenceCard";
import { ConfidenceLevelLabel } from "./constants";

interface ConfidenceRowProps extends HTMLAttributes<HTMLDivElement> {
  confidenceCounts: {
    highConfidenceCount: number;
    mediumConfidenceCount: number;
    lowConfidenceCount: number;
  };
  reviewHref: string;
  monitorId: string;
}

export interface ConfidenceCardItem {
  label: string;
  count: number;
  severity: ConfidenceBucket;
}

export const ConfidenceRow = ({
  confidenceCounts,
  reviewHref,
  monitorId,
  ...props
}: ConfidenceRowProps) => {
  const dataSource = useMemo<ConfidenceCardItem[]>(
    () =>
      [
        {
          label: ConfidenceLevelLabel.HIGH,
          count: confidenceCounts.highConfidenceCount,
          severity: ConfidenceBucket.HIGH,
        },
        {
          label: ConfidenceLevelLabel.MEDIUM,
          count: confidenceCounts.mediumConfidenceCount,
          severity: ConfidenceBucket.MEDIUM,
        },
        {
          label: ConfidenceLevelLabel.LOW,
          count: confidenceCounts.lowConfidenceCount,
          severity: ConfidenceBucket.LOW,
        },
      ].filter((item) => item.count > 0),
    [confidenceCounts],
  );

  return (
    <ExitGrid<ConfidenceCardItem>
      dataSource={dataSource}
      itemKey={(item) => item.severity}
      columns={3}
      gutter={4}
      renderItem={(item) => (
        <ConfidenceCard
          item={item}
          reviewHref={reviewHref}
          monitorId={monitorId}
        />
      )}
      {...props}
    />
  );
};
