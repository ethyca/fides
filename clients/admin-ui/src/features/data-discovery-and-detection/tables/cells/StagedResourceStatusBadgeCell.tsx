import { BadgeCell } from "~/features/common/table/v2";
import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";
import findResourceChangeType from "~/features/data-discovery-and-detection/utils/findResourceChangeType";
import { StagedResource } from "~/types/api";

const statusPropMap: {
  [key in ResourceChangeType]?: { color: string; label: string };
} = {
  [ResourceChangeType.MUTED]: {
    color: "marble",
    label: "Unmonitored",
  },
  [ResourceChangeType.MONITORED]: {
    color: "success",
    label: "Monitoring",
  },
  [ResourceChangeType.IN_PROGRESS]: {
    color: "info",
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
    return <BadgeCell color="success" value="Reviewed" />;
  }
  const changeType = changeTypeOverride ?? findResourceChangeType(result);

  return (
    <BadgeCell
      color={statusPropMap[changeType]?.color ?? "warning"}
      value={statusPropMap[changeType]?.label ?? "Pending review"}
    />
  );
};

export default ResultStatusBadgeCell;
