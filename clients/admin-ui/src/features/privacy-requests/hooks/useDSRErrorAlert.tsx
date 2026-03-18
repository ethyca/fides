import {
  ChakraBox as Box,
  ChakraText as Text,
  useChakraToast as useToast,
  useMessage,
} from "fidesui";
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
  const message = useMessage();
  const toast = useToast();
  const [hasAlert, setHasAlert] = useState(false);
  const [requests, setRequests] = useState<Requests>({
    count: 0,
    total: 0,
  });
  const [skip, setSkip] = useState(true);
  const TOAST_ID = "dsrErrorAlert";
  const DEFAULT_POLLING_INTERVAL = 15000;
  const STATUS = PrivacyRequestStatus.ERROR;

  const { data: notification } = useGetNotificationQuery();
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
    setSkip(!(notification && notification.notify_after_failures > 0));
  }, [notification]);

  useEffect(() => {
    const total = data?.total || 0;

    if (
      total >= (notification?.notify_after_failures || 0) &&
      total > requests.total
    ) {
      setRequests({ count: total - requests.total, total });
      setHasAlert(true);
    } else {
      setHasAlert(false);
    }
  }, [data?.total, notification?.notify_after_failures, requests.total]);

  const processing = () => {
    if (!hasAlert) {
      return;
    }
    message.error({
      content: (
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
      // Cleanup: close toast on unmount
      () => {
        if (toast.isActive(TOAST_ID)) {
          toast.close(TOAST_ID);
        }
      },
    [toast],
  );

  return { processing };
};
