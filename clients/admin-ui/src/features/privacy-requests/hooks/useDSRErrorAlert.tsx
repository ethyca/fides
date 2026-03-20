import { ChakraBox as Box, ChakraText as Text, useNotification } from "fidesui";
import { useEffect, useState } from "react";

import { PrivacyRequestStatus } from "~/types/api";

import {
  useGetAllPrivacyRequestsQuery,
  useGetNotificationQuery,
} from "../privacy-requests.slice";

type Requests = {
  /**
   * Number of new requests
   */
  count: number;
  /**
   * Total number of requests
   */
  total: number;
};

export const useDSRErrorAlert = () => {
  const notification = useNotification();
  const [hasAlert, setHasAlert] = useState(false);
  const [requests, setRequests] = useState<Requests>({
    count: 0,
    total: 0,
  });
  const [skip, setSkip] = useState(true);
  const TOAST_ID = "dsrErrorAlert";
  const DEFAULT_POLLING_INTERVAL = 15000;
  const STATUS = PrivacyRequestStatus.ERROR;

  const { data: notificationData } = useGetNotificationQuery();
  const { data } = useGetAllPrivacyRequestsQuery(
    {
      status: [STATUS],
    },
    {
      pollingInterval: DEFAULT_POLLING_INTERVAL,
      skip,
    },
  );

  useEffect(() => {
    setSkip(!(notificationData && notificationData.notify_after_failures > 0));
  }, [notificationData]);

  useEffect(() => {
    const total = data?.total || 0;

    if (
      total >= (notificationData?.notify_after_failures || 0) &&
      total > requests.total
    ) {
      setRequests({ count: total - requests.total, total });
      setHasAlert(true);
    } else {
      setHasAlert(false);
    }
  }, [data?.total, notificationData?.notify_after_failures, requests.total]);

  const processing = () => {
    if (!hasAlert) {
      return;
    }
    notification.error({
      message: "DSR Error",
      description: (
        <Box>
          DSR automation has failed for{" "}
          <Text as="span" fontWeight="semibold">
            {requests.count}
          </Text>{" "}
          privacy request(s). Please review the event log for further details.
        </Box>
      ),
      duration: 0,
      key: TOAST_ID,
    });
  };

  useEffect(
    () =>
      // Cleanup: close notification on unmount
      () => {
        notification.destroy(TOAST_ID);
      },
    [notification],
  );

  return { processing };
};
