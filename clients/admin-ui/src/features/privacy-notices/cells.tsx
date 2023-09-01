import { Box, Tag, TagProps, Tooltip } from "@fidesui/react";
import React from "react";
import { CellProps } from "react-table";

import { EnableCell, MapCell } from "~/features/common/table/";
import { MECHANISM_MAP } from "~/features/privacy-notices/constants";
import { usePatchPrivacyNoticesMutation } from "~/features/privacy-notices/privacy-notices.slice";
import { PrivacyNoticeResponse } from "~/types/api";

export const MechanismCell = (
  cellProps: CellProps<typeof MECHANISM_MAP, string>
) => <MapCell map={MECHANISM_MAP} {...cellProps} />;

type TagNames = "Suggested" | "Active";

const systemsApplicableTags: Record<TagNames, TagProps & { tooltip: string }> =
  {
    Suggested: {
      backgroundColor: "orange.500",
      color: "white",
      tooltip:
        "Fides has detected systems which would apply to this notice if it were enabled.",
    },
    Active: {
      backgroundColor: "green.500",
      color: "white",
      tooltip: "Fides has detected systems which apply to this notice.",
    },
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

  let tagValue: TagNames | undefined;
  const { systems_applicable: systemsApplicable, disabled } = row.original;
  if (systemsApplicable) {
    tagValue = disabled ? "Suggested" : "Active";
  }
  const { tooltip = undefined, ...tagProps } = tagValue
    ? systemsApplicableTags[tagValue]
    : {};

  return (
    <EnableCell<PrivacyNoticeResponse>
      {...cellProps}
      onToggle={onToggle}
      title="Disable privacy notice"
      message="Are you sure you want to disable this privacy notice? Disabling this
            notice means your users will no longer see this explanation about
            your data uses which is necessary to ensure compliance."
    >
      {tagValue ? (
        <Box mt="2">
          <Tooltip label={tooltip}>
            <Tag
              size="sm"
              width="fit-content"
              {...tagProps}
              data-testid="systems-applicable-tag"
            >
              {tagValue}
            </Tag>
          </Tooltip>
        </Box>
      ) : null}
    </EnableCell>
  );
};
