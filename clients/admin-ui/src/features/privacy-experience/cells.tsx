import { useState } from "react";

import { EnableCell } from "~/features/common/table/cells/EnableCell";
import { useLimitedPatchExperienceConfigMutation } from "~/features/privacy-experience/privacy-experience.slice";
import { ExperienceConfigListViewResponse } from "~/types/api";

export const EnablePrivacyExperienceCell = ({
  record,
}: {
  record: ExperienceConfigListViewResponse;
}) => {
  const [limitedPatchExperienceMutationTrigger] =
    useLimitedPatchExperienceConfigMutation();
  const [isLoading, setIsLoading] = useState(false);

  const onToggle = async (toggle: boolean) => {
    setIsLoading(true);
    const response = await limitedPatchExperienceMutationTrigger({
      id: record.id,
      disabled: !toggle,
    });
    setIsLoading(false);
    return response;
  };

  const { disabled, regions } = record;
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
