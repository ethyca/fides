import { CUSTOM_TAG_COLOR } from "fidesui";

import { BadgeCell } from "~/features/common/table/v2";
import { ResourceChangeType } from "~/features/data-discovery-and-detection/types/ResourceChangeType";
import findResourceChangeType from "~/features/data-discovery-and-detection/utils/findResourceChangeType";
import { StagedResource } from "~/types/api";

const statusPropMap: {
  [key in ResourceChangeType]?: { color: CUSTOM_TAG_COLOR; label: string };
} = {
  [ResourceChangeType.MUTED]: {
    color: CUSTOM_TAG_COLOR.MARBLE,
    label: "Unmonitored",
  },
  [ResourceChangeType.MONITORED]: {
    color: CUSTOM_TAG_COLOR.SUCCESS,
    label: "Monitoring",
  },
  [ResourceChangeType.IN_PROGRESS]: {
    color: CUSTOM_TAG_COLOR.INFO,
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
    return <BadgeCell color={CUSTOM_TAG_COLOR.SUCCESS} value="Reviewed" />;
  }
  const changeType = changeTypeOverride ?? findResourceChangeType(result);

  return (
    <BadgeCell
      color={statusPropMap[changeType]?.color ?? CUSTOM_TAG_COLOR.WARNING}
      value={statusPropMap[changeType]?.label ?? "Pending review"}
    />
  );
};

export default ResultStatusBadgeCell;
