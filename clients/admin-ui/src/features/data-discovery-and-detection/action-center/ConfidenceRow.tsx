import { AntList as List } from "fidesui";

import { ConfidenceBucket } from "~/types/api/models/ConfidenceBucket";

import { ConfidenceCard } from "./ConfidenceCard";
import { ConfidenceLevelLabel } from "./constants";

interface ConfidenceRowProps {
  highConfidenceCount: number;
  mediumConfidenceCount: number;
  lowConfidenceCount: number;
  reviewHref: string;
  monitorId: string;
}

export const ConfidenceRow = ({
  highConfidenceCount = 0,
  mediumConfidenceCount = 0,
  lowConfidenceCount = 0,
  reviewHref,
  monitorId,
}: ConfidenceRowProps) => {
  if (!highConfidenceCount && !mediumConfidenceCount && !lowConfidenceCount) {
    return null;
  }

  return (
    <List
      grid={{ gutter: 16, column: 3 }}
      dataSource={[
        {
          label: ConfidenceLevelLabel.HIGH,
          count: highConfidenceCount,
          severity: ConfidenceBucket.HIGH,
        },
        {
          label: ConfidenceLevelLabel.MEDIUM,
          count: mediumConfidenceCount,
          severity: ConfidenceBucket.MEDIUM,
        },
        {
          label: ConfidenceLevelLabel.LOW,
          count: lowConfidenceCount,
          severity: ConfidenceBucket.LOW,
        },
      ].filter((item) => item.count > 0)}
      renderItem={(item) => (
        <List.Item>
          <ConfidenceCard item={item} reviewHref={reviewHref} monitorId={monitorId} />
        </List.Item>
      )}
    />
  );
};
