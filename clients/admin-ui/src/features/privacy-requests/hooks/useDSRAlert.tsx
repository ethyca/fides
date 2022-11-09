import { Box, Text, useToast } from "@fidesui/react";
import { useEffect, useState } from "react";

import { useAlert } from "~/features/common/hooks";

import { PrivacyRequest } from "../types";

export const useDSRAlert = (requests: PrivacyRequest[] | undefined) => {
  const toast = useToast();
  const { errorAlert } = useAlert();
  const [errorRequests, setErrorRequests] = useState([] as PrivacyRequest[]);
  const DEFAULT_POLLING_INTERVAL = 15000;
  const PROCESSING_ERRORS_ALERT_ID = "processingErrorsAlert";
  const STATUS = "pending";

  useEffect(() => {
    const getDifference = (
      array1: PrivacyRequest[],
      array2: PrivacyRequest[]
    ) =>
      array1.filter(
        (object1) => !array2.some((object2) => object1.id === object2.id)
      );

    if (requests?.some((item) => item.status === STATUS)) {
      const newErrorRequests = getDifference(
        requests.filter((item) => item.status === STATUS),
        errorRequests
      );
      if (newErrorRequests.length > 0) {
        setErrorRequests(newErrorRequests);
      }
    }
    return () => {
      if (toast.isActive(PROCESSING_ERRORS_ALERT_ID)) {
        toast.close(PROCESSING_ERRORS_ALERT_ID);
      }
    };
  }, [errorRequests, requests, toast]);

  const processingErrorsAlert = () => {
    if (
      toast.isActive(PROCESSING_ERRORS_ALERT_ID) ||
      errorRequests.length === 0
    ) {
      return;
    }
    errorAlert(
      <Box>
        DSR automation has failed for{" "}
        <Text as="span" fontWeight="semibold">
          {errorRequests.length}
        </Text>{" "}
        privacy request(s). Please review the event log for further details.
      </Box>,
      undefined,
      {
        containerStyle: { maxWidth: "max-content" },
        duration: null,
        id: PROCESSING_ERRORS_ALERT_ID,
      }
    );
  };

  return { DEFAULT_POLLING_INTERVAL, processingErrorsAlert };
};
