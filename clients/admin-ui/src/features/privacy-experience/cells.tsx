import { Text } from "@fidesui/react";
import React from "react";
import { CellProps } from "react-table";

import { EnableCell } from "~/features/common/table/";
import { ExperienceConfigResponse } from "~/types/api";

import { COMPONENT_MAP } from "./constants";
import { usePatchExperienceConfigMutation } from "./privacy-experience.slice";

export const ComponentCell = ({
  value,
}: CellProps<ExperienceConfigResponse, string>) => (
  <Text>{COMPONENT_MAP.get(value) ?? value}</Text>
);

export const EnablePrivacyExperienceCell = (
  cellProps: CellProps<ExperienceConfigResponse, boolean>
) => {
  const [patchExperienceMutationTrigger] = usePatchExperienceConfigMutation();

  const { row } = cellProps;
  const onToggle = async (toggle: boolean) => {
    await patchExperienceMutationTrigger({
      id: row.original.id,
      disabled: !toggle,
      regions: row.original.regions,
    });
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
    <EnableCell<ExperienceConfigResponse>
      {...cellProps}
      onToggle={onToggle}
      title={title}
      message={message}
    />
  );
};
