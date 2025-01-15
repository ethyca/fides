import type { BadgeProps } from "fidesui";

import { BadgeCell } from "~/features/common/table/v2";
import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";
import findResourceChangeType from "~/features/data-discovery-and-detection/utils/findResourceChangeType";
import { StagedResource } from "~/types/api";

const statusPropMap: {
  [key in ResourceChangeType]?: BadgeProps & { label: string };
} = {
  [ResourceChangeType.MUTED]: {
    colorScheme: "gray",
    label: "Unmonitored",
  },
  [ResourceChangeType.MONITORED]: {
    colorScheme: "green",
    label: "Monitoring",
  },
  [ResourceChangeType.IN_PROGRESS]: {
    colorScheme: "blue",
    label: "Classifying",
  },
};

const ResultStatusBadgeCell = ({
  result,
  changeTypeOverride,
}: {
  result: StagedResource;
  changeTypeOverride?: ResourceChangeType;
}) => {
  if (result.user_assigned_data_categories?.length) {
    return <BadgeCell colorScheme="green" value="Reviewed" />;
  }
  const changeType = changeTypeOverride ?? findResourceChangeType(result);

  return (
    <BadgeCell
      colorScheme={statusPropMap[changeType]?.colorScheme ?? "orange"}
      value={statusPropMap[changeType]?.label ?? "Pending review"}
    />
  );
};

export default ResultStatusBadgeCell;
