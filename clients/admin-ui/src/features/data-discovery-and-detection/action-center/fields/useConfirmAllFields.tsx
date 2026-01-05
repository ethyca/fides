import { useMessage, useModal } from "fidesui";

import { pluralize } from "~/features/common/utils";
import { ConfidenceBucket } from "~/types/api/models/ConfidenceBucket";
import { FieldActionType } from "~/types/api/models/FieldActionType";
import { isErrorResult } from "~/types/errors";

import {
  FIELD_ACTION_CONFIRMATION_MESSAGE,
  FIELD_ACTION_INTERMEDIATE,
  FIELD_ACTION_LABEL,
} from "./FieldActions.const";
import { useFieldActionsMutation } from "./monitor-fields.slice";
import { getActionErrorMessage, getActionModalProps } from "./utils";

export const useConfirmAllFields = (monitorId: string) => {
  const modalApi = useModal();
  const [bulkAction] = useFieldActionsMutation();
  const messageApi = useMessage();

  const confirmAll = async (
    confidenceBucket: ConfidenceBucket,
    count: number,
  ) => {
    const actionType = FieldActionType.PROMOTE;
    const key = Date.now();

    const confirmed = await modalApi.confirm(
      getActionModalProps(
        FIELD_ACTION_LABEL[actionType],
        FIELD_ACTION_CONFIRMATION_MESSAGE[actionType](count),
      ),
    );

    if (!confirmed) {
      return;
    }

    messageApi.open({
      key,
      type: "loading",
      content: `${FIELD_ACTION_INTERMEDIATE[actionType]} ${count} ${pluralize(count, "field", "fields")}...`,
      duration: 0,
    });

    const mutationResult = await bulkAction({
      query: {
        confidence_bucket: [confidenceBucket],
      },
      path: {
        monitor_config_id: monitorId,
        action_type: actionType,
      },
      body: {
        excluded_resource_urns: [],
      },
    });

    if (isErrorResult(mutationResult)) {
      messageApi.open({
        key,
        type: "error",
        content: getActionErrorMessage(actionType),
        duration: 5,
      });

      return;
    }

    messageApi.open({
      key,
      type: "success",
      content: `${count} ${pluralize(count, "field", "fields")} approved — stronger governance, less busywork.`,
      duration: 10,
    });
  };

  return { confirmAll };
};
