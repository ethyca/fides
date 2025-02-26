import {
  AntButton as Button,
  Box,
  forwardRef,
  RepeatClockIcon,
  Text,
} from "fidesui";
import { ForwardedRef, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";

import {
  selectRetryRequests,
  setRetryRequests,
  useBulkRetryMutation,
  useRetryMutation,
} from "../privacy-requests.slice";
import { PrivacyRequestEntity } from "../types";

type ReprocessButtonProps = {
  handleBlur?: (ref: ForwardedRef<any>) => void;
  subjectRequest?: PrivacyRequestEntity;
};

const ReprocessButton = forwardRef(
  ({ handleBlur, subjectRequest }: ReprocessButtonProps, ref) => {
    const dispatch = useAppDispatch();
    const [isReprocessing, setIsReprocessing] = useState(false);
    const { errorAlert, successAlert } = useAlert();

    const { errorRequests } = useAppSelector(selectRetryRequests);
    const [bulkRetry] = useBulkRetryMutation();
    const [retry] = useRetryMutation();

    const handleBulkReprocessClick = async () => {
      setIsReprocessing(true);
      const payload = await bulkRetry(errorRequests);
      if ("error" in payload) {
        dispatch(setRetryRequests({ checkAll: false, errorRequests: [] }));
        errorAlert(
          getErrorMessage(payload.error),
          `DSR batch automation has failed due to the following:`,
          { duration: null },
        );
      } else {
        if (payload.data.failed.length > 0) {
          errorAlert(
            <Box>
              DSR automation has failed for{" "}
              <Text as="span" fontWeight="semibold">
                {payload.data.failed.length}
              </Text>{" "}
              privacy request(s). Please review the event log for further
              details.
            </Box>,
            undefined,
            { containerStyle: { maxWidth: "max-content" }, duration: null },
          );
        }
        if (payload.data.succeeded.length > 0) {
          successAlert(`Privacy request(s) are now being reprocessed.`);
        }
      }
      setIsReprocessing(false);
    };

    const handleSingleReprocessClick = async () => {
      if (!subjectRequest) {
        return;
      }
      setIsReprocessing(true);
      const payload = await retry(subjectRequest);
      if ("error" in payload) {
        errorAlert(
          getErrorMessage(payload.error),
          `DSR automation has failed for this privacy request due to the following:`,
          { duration: null },
        );
      } else {
        successAlert(`Privacy request is now being reprocessed.`);
      }
      setIsReprocessing(false);

      if (handleBlur) {
        handleBlur(ref);
      }
    };

    return (
      <Button
        disabled={isReprocessing}
        loading={isReprocessing}
        onClick={
          subjectRequest ? handleSingleReprocessClick : handleBulkReprocessClick
        }
        ref={ref}
        size="small"
        icon={<RepeatClockIcon />}
      >
        Reprocess
      </Button>
    );
  },
);

export default ReprocessButton;
