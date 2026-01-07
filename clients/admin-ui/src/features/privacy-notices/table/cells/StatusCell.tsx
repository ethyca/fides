import { CUSTOM_TAG_COLOR } from "fidesui";

import TagCell from "~/features/common/table/cells/TagCell";
import { NoticeStatus } from "~/features/privacy-notices/table/getNoticeStatus";

const VALUE_TO_TAG_PROPS_MAP: Record<
  NoticeStatus,
  { color: CUSTOM_TAG_COLOR; tooltip: string }
> = {
  [NoticeStatus.AVAILABLE]: {
    color: CUSTOM_TAG_COLOR.WARNING,
    tooltip:
      "This notice is associated with a system + data use and can be enabled",
  },
  [NoticeStatus.ENABLED]: {
    color: CUSTOM_TAG_COLOR.SUCCESS,
    tooltip: "This notice is active and available for consumers",
  },
  [NoticeStatus.INACTIVE]: {
    color: CUSTOM_TAG_COLOR.DEFAULT,
    tooltip:
      "This privacy notice cannot be enabled because it either does not have a data use or the linked data use has not been assigned to a system",
  },
};

const StatusCell = ({ status }: { status: NoticeStatus }) => {
  const { tooltip, color } = VALUE_TO_TAG_PROPS_MAP[status];

  return (
    <TagCell
      value={status}
      tooltip={tooltip}
      color={color}
      data-testid="status-badge"
      style={{ textTransform: "uppercase" }}
    />
  );
};

export default StatusCell;
