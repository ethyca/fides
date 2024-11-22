import { CellContext } from "@tanstack/react-table";
import React, { useState } from "react";

import { DefaultCell, EnableCell } from "~/features/common/table/v2/cells";
import { COMPONENT_MAP } from "~/features/privacy-experience/constants";
import { useLimitedPatchExperienceConfigMutation } from "~/features/privacy-experience/privacy-experience.slice";
import { ComponentType, ExperienceConfigListViewResponse } from "~/types/api";

export const ComponentCell = (value: ComponentType | undefined) => {
  const innerText = COMPONENT_MAP.get(value!) ?? value;
  return <DefaultCell value={innerText} />;
};

export const EnablePrivacyExperienceCell = ({
  row,
  getValue,
}: CellContext<ExperienceConfigListViewResponse, boolean | undefined>) => {
  const [limitedPatchExperienceMutationTrigger] =
    useLimitedPatchExperienceConfigMutation();
  const [isLoading, setIsLoading] = useState(false);

  const onToggle = async (toggle: boolean) => {
    setIsLoading(true);
    const response = await limitedPatchExperienceMutationTrigger({
      id: row.original.id,
      disabled: !toggle,
    });
    setIsLoading(false);
    return response;
  };

  const disabled = getValue()!;
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
      enabled={!disabled}
      onToggle={onToggle}
      title={title}
      message={message}
      loading={isLoading}
    />
  );
};
