import { Badge, TagProps, Tooltip } from "@fidesui/react";
import React from "react";
import { CellProps } from "react-table";

import { EnableCell, MapCell } from "~/features/common/table/";
import {
  FRAMEWORK_MAP,
  MECHANISM_MAP,
} from "~/features/privacy-notices/constants";
import { useLimitedPatchPrivacyNoticesMutation } from "~/features/privacy-notices/privacy-notices.slice";
import { PrivacyNoticeResponse } from "~/types/api";

export const MechanismCell = (
  cellProps: CellProps<typeof MECHANISM_MAP, string>
) => <MapCell map={MECHANISM_MAP} {...cellProps} />;

export const FrameworkCell = (
  cellProps: CellProps<typeof FRAMEWORK_MAP, string>
) => <MapCell map={FRAMEWORK_MAP} {...cellProps} />;

type TagNames = "available" | "enabled" | "inactive";

const systemsApplicableTags: Record<TagNames, TagProps & { tooltip: string }> =
  {
    available: {
      backgroundColor: "orange.100",
      color: "orange.800",
      tooltip:
        "This notice is associated with a system + data use and can be enabled",
    },
    enabled: {
      backgroundColor: "green.100",
      color: "green.800",
      tooltip: "This notice is active and available for consumers",
    },
    inactive: {
      backgroundColor: "gray.100",
      color: "gray.800",
      tooltip:
        "This privacy notice cannot be enabled because it either does not have a data use or the linked data use has not been assigned to a system",
    },
  };

export const EnablePrivacyNoticeCell = (
  cellProps: CellProps<PrivacyNoticeResponse, boolean>
) => {
  const [patchNoticeMutationTrigger] = useLimitedPatchPrivacyNoticesMutation();

  const { row } = cellProps;
  const onToggle = async (toggle: boolean) =>
    patchNoticeMutationTrigger({
      id: row.original.id,
      disabled: !toggle,
    });

  const {
    systems_applicable: systemsApplicable,
    disabled: noticeIsDisabled,
    data_uses: dataUses,
  } = row.original;
  const hasDataUses = !!dataUses;
  const toggleIsDisabled =
    (noticeIsDisabled && !systemsApplicable) || !hasDataUses;

  return (
    <EnableCell<PrivacyNoticeResponse>
      {...cellProps}
      isDisabled={toggleIsDisabled}
      onToggle={onToggle}
      title="Disable privacy notice"
      message="Are you sure you want to disable this privacy notice? Disabling this
            notice means your users will no longer see this explanation about
            your data uses which is necessary to ensure compliance."
    />
  );
};

export const PrivacyNoticeStatusCell = (
  cellProps: CellProps<PrivacyNoticeResponse, boolean>
) => {
  const { row } = cellProps;

  let tagValue: TagNames | undefined;
  const {
    systems_applicable: systemsApplicable,
    disabled,
    data_uses: dataUses,
  } = row.original;
  if (!dataUses) {
    tagValue = "inactive";
  } else if (systemsApplicable) {
    tagValue = disabled ? "available" : "enabled";
  } else {
    tagValue = "inactive";
  }
  const { tooltip = undefined, ...tagProps } = tagValue
    ? systemsApplicableTags[tagValue]
    : {};

  return (
    <Tooltip label={tooltip}>
      <Badge
        size="sm"
        width="fit-content"
        {...tagProps}
        data-testid="status-badge"
        textTransform="uppercase"
        fontWeight="400"
        color="gray.600"
        px={2}
      >
        {tagValue}
      </Badge>
    </Tooltip>
  );
};
