import React from "react";
import { CellProps } from "react-table";

import { EnableCell } from "~/features/common/table/";
import { PrivacyExperienceResponse } from "~/types/api";

export const EnablePrivacyExperienceCell = (
  cellProps: CellProps<PrivacyExperienceResponse, boolean>
) => {
  // TODO: replace with real API call once it is ready
  const mockPatch = (payload: any) => {
    console.log("patch", payload);
  };

  const { row } = cellProps;
  const onToggle = async (toggle: boolean) => {
    await mockPatch([
      {
        id: row.original.id,
        disabled: !toggle,
      },
    ]);
  };

  const { regions } = row.original;
  const multipleRegions = regions ? regions.length > 1 : false;

  const title = multipleRegions
    ? "Disabling multiple states"
    : "Disabling experience";
  const message = multipleRegions
    ? "Warning, you are about to disable this privacy experience for multiple states. If you continue, your privacy notices will not be accessible to users in these locations."
    : "Warning, you are about to disable this privacy experience. If you continue, your privacy notices will not be accessible to users in this location.";

  return (
    <EnableCell<PrivacyExperienceResponse>
      {...cellProps}
      onToggle={onToggle}
      title={title}
      message={message}
    />
  );
};
