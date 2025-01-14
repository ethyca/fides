import { CellContext } from "@tanstack/react-table";
import { Badge, TagProps, Tooltip } from "fidesui";
import React, { useState } from "react";

import { PRIVACY_NOTICE_REGION_MAP } from "~/features/common/privacy-notice-regions";
import { EnableCell } from "~/features/common/table/v2/cells";
import { MECHANISM_MAP } from "~/features/privacy-notices/constants";
import { useLimitedPatchPrivacyNoticesMutation } from "~/features/privacy-notices/privacy-notices.slice";
import {
  ConsentMechanism,
  LimitedPrivacyNoticeResponseSchema,
  PrivacyNoticeRegion,
} from "~/types/api";

export const MechanismCell = (value: ConsentMechanism | undefined) => {
  const innerText = MECHANISM_MAP.get(value!) ?? value;
  return (
    <Badge
      size="sm"
      width="fit-content"
      data-testid="status-badge"
      textTransform="uppercase"
      fontWeight="400"
      px={2}
    >
      {innerText}
    </Badge>
  );
};

export const getRegions = (
  regions: PrivacyNoticeRegion[] | undefined,
): string[] => {
  if (!regions) {
    return [];
  }
  const values: string[] = [];
  regions.forEach((region) => {
    const value = PRIVACY_NOTICE_REGION_MAP.get(region);
    if (value !== undefined) {
      values.push(value);
    }
  });
  return values;
};

export const getNoticeChildren = (
  children: LimitedPrivacyNoticeResponseSchema[] | undefined | null,
): string[] => {
  if (!children) {
    return [];
  }
  const values: string[] = [];
  children.forEach((child) => {
    const value = child.name;
    if (value !== undefined) {
      values.push(value);
    }
  });
  return values;
};

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

export const PrivacyNoticeStatusCell = (
  cellProps: CellContext<LimitedPrivacyNoticeResponseSchema, boolean>,
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
        px={2}
      >
        {tagValue}
      </Badge>
    </Tooltip>
  );
};

export const EnablePrivacyNoticeCell = ({
  row,
  getValue,
}: CellContext<LimitedPrivacyNoticeResponseSchema, boolean>) => {
  const [patchNoticeMutationTrigger] = useLimitedPatchPrivacyNoticesMutation();
  const [isLoading, setIsLoading] = useState(false);

  const disabled = getValue();
  const onToggle = async (toggle: boolean) => {
    setIsLoading(true);
    const response = await patchNoticeMutationTrigger({
      id: row.original.id,
      disabled: !toggle,
    });
    setIsLoading(false);
    return response;
  };

  const {
    systems_applicable: systemsApplicable,
    disabled: noticeIsDisabled,
    data_uses: dataUses,
  } = row.original;
  const hasDataUses = !!dataUses;
  const toggleIsDisabled =
    (noticeIsDisabled && !systemsApplicable) || !hasDataUses;

  return (
    <EnableCell
      enabled={!disabled}
      isDisabled={toggleIsDisabled}
      onToggle={onToggle}
      title="Disable privacy notice"
      message="Are you sure you want to disable this privacy notice? Disabling this
            notice means your users will no longer see this explanation about
            your data uses which is necessary to ensure compliance."
      loading={isLoading}
    />
  );
};
