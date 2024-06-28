import { getErrorMessage } from "common/helpers";
import { useToast } from "fidesui";

import { errorToastParams, successToastParams } from "~/features/common/toast";
import { usePatchMessagingTemplateByIdMutation } from "~/features/messaging-templates/messaging-templates.slice";
import { isErrorResult } from "~/types/errors";

const useMessagingTemplateToggle = () => {
  const toast = useToast();
  const [patchMessagingTemplateById] = usePatchMessagingTemplateByIdMutation();

  const toggleIsTemplateEnabled = async ({
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
        `Messaging template ${isEnabled ? "enabled" : "disabled"}`
      )
    );
  };

  return { toggleIsTemplateEnabled };
};
export default useMessagingTemplateToggle;
