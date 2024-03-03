import { Badge } from "@fidesui/react";
import { CellContext } from "@tanstack/react-table";
import React from "react";

import { ComponentType, ExperienceConfigListViewResponse } from "~/types/api";

import { EnableCell } from "../common/table/v2/cells";
import { COMPONENT_MAP } from "./constants";
import { useLimitedPatchExperienceConfigMutation } from "./privacy-experience.slice";

export const ComponentCell = (value: ComponentType | undefined) => {
  const innerText = COMPONENT_MAP.get(value!) ?? value;
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
      {innerText}
    </Badge>
  );
};

export const EnablePrivacyExperienceCell = ({
  row,
  getValue,
}: CellContext<ExperienceConfigListViewResponse, boolean | undefined>) => {
  const [limitedPatchExperienceMutationTrigger] =
    useLimitedPatchExperienceConfigMutation();

  const onToggle = async (toggle: boolean) =>
    limitedPatchExperienceMutationTrigger({
      id: row.original.id,
      disabled: !toggle,
    });

  const value = getValue()!;
  const { regions } = row.original;
  const multipleRegions = regions ? regions.length > 1 : false;

  const title = multipleRegions
    ? "Disabling multiple states"
    : "Disabling experience";
  const message = multipleRegions
    ? "Warning, you are about to disable this privacy experience for multiple locations. If you continue, your privacy notices will not be accessible to users in these locations."
    : "Warning, you are about to disable this privacy experience. If you continue, your privacy notices will not be accessible to users in this location.";

  return (
    <EnableCell
      value={value}
      onToggle={onToggle}
      title={title}
      message={message}
    />
  );
};
