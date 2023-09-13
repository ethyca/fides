import { Badge, TagProps, Tooltip } from "@fidesui/react";
import React from "react";
import { CellProps } from "react-table";

import { PRIVACY_NOTICE_REGION_MAP } from "~/features/common/privacy-notice-regions";
import { EnableCell, MapCell, MultiTagCell } from "~/features/common/table/";
import { MECHANISM_MAP } from "~/features/privacy-notices/constants";
import { usePatchPrivacyNoticesMutation } from "~/features/privacy-notices/privacy-notices.slice";
import { PrivacyNoticeResponse } from "~/types/api";

export const MechanismCell = (
  cellProps: CellProps<PrivacyNoticeResponse, string>
) => {
  const tagValue = MECHANISM_MAP.get(cellProps.row.original.consent_mechanism);
  return (
    <Badge
      size="sm"
      width="fit-content"
      data-testid="status-badge"
      textTransform="uppercase"
      fontWeight="400"
      color="gray.600"
      px={2}
    >
      {tagValue}
    </Badge>
  );
};
{
  /* <MapCell map={MECHANISM_MAP} {...cellProps} />; */
}

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
        "This privacy notice cannot be enabled because the linked data use has not been assigned to a system",
    },
  };

export const LocationCell = (
  cellProps: CellProps<PrivacyNoticeResponse, string[]>
) => {
  const regions = cellProps.row.original.regions;
  let tagValue = undefined;
  if (regions.length > 1) {
    tagValue = regions.length + " locations";
  } else {
    tagValue = PRIVACY_NOTICE_REGION_MAP.get(regions[0]);
  }
  return (
    <Badge
      size="sm"
      width="fit-content"
      data-testid="status-badge"
      textTransform="uppercase"
      fontWeight="400"
      color="gray.600"
      px={2}
    >
      {tagValue}
    </Badge>
  );
};

export const EnablePrivacyNoticeCell = (
  cellProps: CellProps<PrivacyNoticeResponse, boolean>
) => {
  const [patchNoticeMutationTrigger] = usePatchPrivacyNoticesMutation();

  const { row } = cellProps;
  const onToggle = async (toggle: boolean) => {
    await patchNoticeMutationTrigger([
      {
        id: row.original.id,
        disabled: !toggle,
      },
    ]);
  };

  const { systems_applicable: systemsApplicable, disabled: noticeIsDisabled } =
    row.original;
  const toggleIsDisabled = noticeIsDisabled && !systemsApplicable;

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
  const { systems_applicable: systemsApplicable, disabled } = row.original;
  if (systemsApplicable) {
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
