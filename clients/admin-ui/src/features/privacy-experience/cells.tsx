import { Text } from "@fidesui/react";
import React from "react";
import { CellProps } from "react-table";

import { EnableCell } from "~/features/common/table/";
import { PrivacyExperienceResponse } from "~/types/api";

import { COMPONENT_MAP } from "./constants";
import { usePatchPrivacyExperienceMutation } from "./privacy-experience.slice";

export const ComponentCell = ({
  value,
}: CellProps<PrivacyExperienceResponse, string>) => (
  <Text>{COMPONENT_MAP.get(value) ?? value}</Text>
);

export const EnablePrivacyExperienceCell = (
  cellProps: CellProps<PrivacyExperienceResponse, boolean>
) => {
  const [patchExperienceMutationTrigger] = usePatchPrivacyExperienceMutation();

  const { row } = cellProps;
  const onToggle = async (toggle: boolean) => {
    await patchExperienceMutationTrigger([
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
