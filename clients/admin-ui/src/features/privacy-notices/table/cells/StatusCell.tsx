import {
  AntTag as Tag,
  AntTooltip as Tooltip,
  CUSTOM_TAG_COLOR,
} from "fidesui";

import { PrivacyNoticeRowType } from "~/features/privacy-notices/table/usePrivacyNoticesTable";

enum TagNames {
  AVAILABLE = "available",
  ENABLED = "enabled",
  INACTIVE = "inactive",
  DEFAULT = "default",
}

const VALUE_TO_TAG_PROPS_MAP: Record<
  TagNames,
  { color: CUSTOM_TAG_COLOR; tooltip?: string }
> = {
  [TagNames.AVAILABLE]: {
    color: CUSTOM_TAG_COLOR.WARNING,
    tooltip:
      "This notice is associated with a system + data use and can be enabled",
  },
  [TagNames.ENABLED]: {
    color: CUSTOM_TAG_COLOR.SUCCESS,
    tooltip: "This notice is active and available for consumers",
  },
  [TagNames.INACTIVE]: {
    color: CUSTOM_TAG_COLOR.DEFAULT,
    tooltip:
      "This privacy notice cannot be enabled because it either does not have a data use or the linked data use has not been assigned to a system",
  },
  [TagNames.DEFAULT]: {
    color: CUSTOM_TAG_COLOR.DEFAULT,
  },
};

const StatusCell = ({ record }: { record: PrivacyNoticeRowType }) => {
  let tagValue: TagNames | undefined;
  const {
    systems_applicable: systemsApplicable,
    disabled,
    data_uses: dataUses,
  } = record;
  if (!dataUses) {
    tagValue = TagNames.INACTIVE;
  } else if (systemsApplicable) {
    tagValue = disabled ? TagNames.AVAILABLE : TagNames.ENABLED;
  } else {
    tagValue = TagNames.INACTIVE;
  }

  const tagProps = VALUE_TO_TAG_PROPS_MAP[tagValue ?? TagNames.DEFAULT];

  const { tooltip, color } = tagProps;

  return (
    <Tooltip title={tooltip}>
      {/* the span is necessary to prevent the tooltip from changing the line height */}
      <span>
        <Tag
          color={color}
          data-testid="status-badge"
          style={{ textTransform: "uppercase" }}
        >
          {tagValue}
        </Tag>
      </span>
    </Tooltip>
  );
};

export default StatusCell;
