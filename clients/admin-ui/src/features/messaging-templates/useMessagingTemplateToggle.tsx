import { getErrorMessage } from "common/helpers";
import { useMessage } from "fidesui";
import { useCallback } from "react";

import { usePatchMessagingTemplateByIdMutation } from "~/features/messaging-templates/messaging-templates.slice.plus";
import { isErrorResult } from "~/types/errors";

const useMessagingTemplateToggle = () => {
  const message = useMessage();
  const [patchMessagingTemplateById] = usePatchMessagingTemplateByIdMutation();

  const toggleIsTemplateEnabled = useCallback(
    async ({
      isEnabled,
      templateId,
    }: {
      isEnabled: boolean;
      templateId: string;
    }) => {
      const result = await patchMessagingTemplateById({
        templateId,
        template: { is_enabled: isEnabled },
      });

      if (isErrorResult(result)) {
        message.error(getErrorMessage(result.error));
        return;
      }

      message.success(
        `Messaging template ${isEnabled ? "enabled" : "disabled"}`,
      );
    },
    [patchMessagingTemplateById, message],
  );

  return { toggleIsTemplateEnabled };
};
export default useMessagingTemplateToggle;
