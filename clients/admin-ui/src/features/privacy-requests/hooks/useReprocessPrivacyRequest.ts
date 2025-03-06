import { antMessage as message } from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import { PrivacyRequestStatus } from "~/types/api";

import { useRetryMutation } from "../privacy-requests.slice";
import { PrivacyRequestEntity } from "../types";

const useReprocessPrivacyRequest = ({
  privacyRequest,
}: {
  privacyRequest: PrivacyRequestEntity;
}) => {
  const { errorAlert, successAlert } = useAlert();
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
      errorAlert(
        getErrorMessage(payload.error),
        `DSR automation has failed for this privacy request due to the following:`,
        { duration: null },
      );
    } else {
      successAlert(`Privacy request is now being reprocessed.`);
    }
    closeMessage();
  };

  return { reprocessPrivacyRequest, showReprocess };
};

export default useReprocessPrivacyRequest;
