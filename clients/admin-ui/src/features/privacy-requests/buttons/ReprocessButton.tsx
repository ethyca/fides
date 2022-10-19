import { Button, ButtonProps, forwardRef } from "@fidesui/react";
import { useState } from "react";

import { useAppSelector } from "~/app/hooks";

import { useAlert, useAPIHelper } from "../../common/hooks";
import {
  selectRetryRequests, useBulkRetryMutation,
  useRetryMutation
} from "../privacy-requests.slice";
import { PrivacyRequest } from "../types";

type ReprocessButtonProps = {
  buttonProps?: ButtonProps;
  subjectRequest?: PrivacyRequest;
};

const ReprocessButton = forwardRef(
  ({ buttonProps, subjectRequest }: ReprocessButtonProps, ref) => {
    const [isReprocessing, setIsReprocessing] = useState(false);
    const { handleError } = useAPIHelper();
    const { successAlert } = useAlert();

    const { errorRequests } = useAppSelector(selectRetryRequests);
    const [bulkRetry] = useBulkRetryMutation();
    const [retry] = useRetryMutation();

    const handleBulkReprocessClick = () => {
      setIsReprocessing(true);
      bulkRetry(errorRequests!)
        .unwrap()
        .then(() => {
          successAlert(`Data subject request(s) are now being reprocessed.`);
        })
        .catch((error) => {
          handleError(error);
        })
        .finally(() => {
          setIsReprocessing(false);
        });
    };

    const handleSingleReprocessClick = () => {
      setIsReprocessing(true);
      retry(subjectRequest!)
        .unwrap()
        .then(() => {
          successAlert(`Data subject request is now being reprocessed.`);
        })
        .catch((error) => {
          handleError(error);
        })
        .finally(() => {
          setIsReprocessing(false);
        });
    };

    return (
      <Button
        {...buttonProps}
        isDisabled={isReprocessing}
        isLoading={isReprocessing}
        loadingText="Reprocessing"
        onClick={
          subjectRequest ? handleSingleReprocessClick : handleBulkReprocessClick
        }
        ref={ref}
        spinnerPlacement="end"
        variant="outline"
        _hover={{
          bg: "gray.100",
        }}
        _loading={{
          opacity: 1,
          div: { opacity: 0.4 },
        }}
      >
        Reprocess
      </Button>
    );
  }
);

export default ReprocessButton;
