import { Button, ButtonProps, forwardRef } from "@fidesui/react";
import React, { useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";

import { useAlert, useAPIHelper } from "../../common/hooks";
import {
  selectErrorRequests,
  setErrorRequests,
  useBulkRetryMutation,
  useRetryMutation,
} from "../privacy-requests.slice";
import { PrivacyRequest } from "../types";

type ReprocessButtonProps = {
  buttonProps?: ButtonProps;
  subjectRequest?: PrivacyRequest;
};

const ReprocessButton = forwardRef(
  ({ buttonProps, subjectRequest }: ReprocessButtonProps, ref) => {
    const dispatch = useAppDispatch();
    const [isReprocessing, setIsReprocessing] = useState(false);
    const { handleError } = useAPIHelper();
    const { successAlert } = useAlert();

    const errorRequests = useAppSelector(selectErrorRequests);
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
          dispatch(setErrorRequests([]));
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
