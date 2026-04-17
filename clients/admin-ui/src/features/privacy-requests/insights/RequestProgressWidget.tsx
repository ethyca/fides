import { ActionType } from "~/types/api/models/ActionType";

import { ProgressCard } from "../../data-discovery-and-detection/action-center/ProgressCard/ProgressCard";
import { buildBucketProgressProps, SlaBucket } from "./utils";

export interface RequestProgressWidgetProps {
  bucket: SlaBucket;
  counts: Record<ActionType, number>;
  lastUpdated?: string;
  isLoading?: boolean;
}

/**
 * Renders a single SLA-bucket ProgressCard (On track / Approaching /
 * Overdue). The stacked bar and bottom badges break the bucket's total
 * down by DSR action type.
 *
 * The card is visually dimmed while loading with no cached data, matching
 * the Action Center's MonitorProgressWidget placeholder behavior.
 */
const RequestProgressWidget = ({
  bucket,
  counts,
  lastUpdated,
  isLoading,
}: RequestProgressWidgetProps) => {
  const hasAnyData = Object.values(counts).some((n) => n > 0);

  return (
    <ProgressCard
      {...buildBucketProgressProps({ bucket, counts, lastUpdated })}
      disabled={isLoading && !hasAnyData}
    />
  );
};

export default RequestProgressWidget;
