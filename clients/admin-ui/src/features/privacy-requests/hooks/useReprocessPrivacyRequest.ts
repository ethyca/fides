import { useMessage } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";
import { PrivacyRequestStatus } from "~/types/api";

import { useRetryMutation } from "../privacy-requests.slice";
import { PrivacyRequestEntity } from "../types";

const useReprocessPrivacyRequest = ({
  privacyRequest,
}: {
  privacyRequest: PrivacyRequestEntity;
}) => {
  const message = useMessage();
  const isErrorStatus = privacyRequest.status === PrivacyRequestStatus.ERROR;
  const showReprocess = isErrorStatus;

  const [retry] = useRetryMutation();

  const reprocessPrivacyRequest = async () => {
    if (!privacyRequest) {
      return;
    }
    const closeMessage = message.loading("Reprocessing privacy request...", 0);
    const payload = await retry(privacyRequest);
    if ("error" in payload) {
      message.error({
        content: getErrorMessage(payload.error!),
        duration: 0,
      });
    } else {
      message.success(`Privacy request is now being reprocessed.`);
    }
    closeMessage();
  };

  return { reprocessPrivacyRequest, showReprocess };
};

export default useReprocessPrivacyRequest;
