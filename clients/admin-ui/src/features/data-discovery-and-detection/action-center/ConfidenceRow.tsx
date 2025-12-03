import { AntList as List, AntListProps as ListProps } from "fidesui";

import { ConfidenceBucket } from "~/types/api/models/ConfidenceBucket";

import { ConfidenceCard, ConfidenceCardItem } from "./ConfidenceCard";
import { ConfidenceLevelLabel } from "./constants";

interface ConfidenceRowProps extends ListProps<ConfidenceCardItem> {
  confidenceCounts: {
    highConfidenceCount: number;
    mediumConfidenceCount: number;
    lowConfidenceCount: number;
  };
  reviewHref: string;
  monitorId: string;
}

export const ConfidenceRow = ({
  confidenceCounts,
  reviewHref,
  monitorId,
  ...props
}: ConfidenceRowProps) => {
  return (
    <List
      grid={{ gutter: 16, column: 3 }}
      dataSource={[
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
      ].filter((item) => item.count > 0)}
      renderItem={(item) => (
        <List.Item>
          <ConfidenceCard
            item={item}
            reviewHref={reviewHref}
            monitorId={monitorId}
          />
        </List.Item>
      )}
      {...props}
    />
  );
};
