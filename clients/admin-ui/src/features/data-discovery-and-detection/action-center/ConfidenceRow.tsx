import { AntList as List } from "fidesui";

import { ConfidenceCard } from "./ConfidenceCard";
import { ConfidenceLevelLabel } from "./constants";

interface ConfidenceRowProps {
  highConfidenceCount: number;
  mediumConfidenceCount: number;
  lowConfidenceCount: number;
  reviewHref: string;
}

export const ConfidenceRow = ({
  highConfidenceCount = 0,
  mediumConfidenceCount = 0,
  lowConfidenceCount = 0,
  reviewHref,
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
          percent: 100,
        },
        {
          label: ConfidenceLevelLabel.MEDIUM,
          count: mediumConfidenceCount,
          percent: 50,
        },
        {
          label: ConfidenceLevelLabel.LOW,
          count: lowConfidenceCount,
          percent: 25,
        },
      ]}
      renderItem={(item) =>
        item.count > 0 && (
          <List.Item>
            <ConfidenceCard item={item} reviewHref={reviewHref} />
          </List.Item>
        )
      }
    />
  );
};
