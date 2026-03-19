import {
  Button,
  ChakraBox as Box,
  chakraForwardRef as forwardRef,
  ChakraRepeatClockIcon as RepeatClockIcon,
  ChakraText as Text,
  useMessage,
} from "fidesui";
import { ForwardedRef, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";

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
    const message = useMessage();

    const { errorRequests } = useAppSelector(selectRetryRequests);
    const [bulkRetry] = useBulkRetryMutation();
    const [retry] = useRetryMutation();

    const handleBulkReprocessClick = async () => {
      setIsReprocessing(true);
      const payload = await bulkRetry(errorRequests);
      if (isErrorResult(payload)) {
        dispatch(setRetryRequests({ checkAll: false, errorRequests: [] }));
        message.error({
          content: `DSR batch automation has failed due to the following: ${getErrorMessage(payload.error)}`,
          duration: 0,
        });
      } else {
        if (payload.data.failed.length > 0) {
          message.error({
            content: (
              <Box>
                DSR automation has failed for{" "}
                <Text as="span" fontWeight="semibold">
                  {payload.data.failed.length}
                </Text>{" "}
                privacy request(s). Please review the event log for further
                details.
              </Box>
            ),
            duration: 0,
          });
        }
        if (payload.data.succeeded.length > 0) {
          message.success(`Privacy request(s) are now being reprocessed.`);
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
      if (isErrorResult(payload)) {
        message.error({
          content: `DSR automation has failed for this privacy request due to the following: ${getErrorMessage(payload.error)}`,
          duration: 0,
        });
      } else {
        message.success(`Privacy request is now being reprocessed.`);
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
