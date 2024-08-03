import { getErrorMessage } from "common/helpers";
import { useToast } from "fidesui";
import { useCallback } from "react";

import { errorToastParams, successToastParams } from "~/features/common/toast";
import { usePatchMessagingTemplateByIdMutation } from "~/features/messaging-templates/messaging-templates.slice.plus";
import { isErrorResult } from "~/types/errors";

const useMessagingTemplateToggle = () => {
  const toast = useToast();
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
        toast(errorToastParams(getErrorMessage(result.error)));
        return;
      }

      toast(
        successToastParams(
          `Messaging template ${isEnabled ? "enabled" : "disabled"}`,
        ),
      );
    },
    [patchMessagingTemplateById, toast],
  );

  return { toggleIsTemplateEnabled };
};
export default useMessagingTemplateToggle;
