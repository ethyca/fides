import React from "react";
import { CellProps } from "react-table";

import { EnableCell, MapCell } from "~/features/common/table/";
import { MECHANISM_MAP } from "~/features/privacy-notices/constants";
import { usePatchPrivacyNoticesMutation } from "~/features/privacy-notices/privacy-notices.slice";
import { PrivacyNoticeResponse } from "~/types/api";

export const MechanismCell = (
  cellProps: CellProps<typeof MECHANISM_MAP, string>
) => <MapCell map={MECHANISM_MAP} {...cellProps} />;

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
  return (
    <EnableCell<PrivacyNoticeResponse>
      {...cellProps}
      onToggle={onToggle}
      title="Disable privacy notice"
      message="Are you sure you want to disable this privacy notice? Disabling this
            notice means your users will no longer see this explanation about
            your data uses which is necessary to ensure compliance."
    />
  );
};
