import { Box, Text } from "fidesui";
import { useEffect, useState } from "react";

import { useAlert } from "~/features/common/hooks";
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
  const { errorAlert } = useAlert();
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
    errorAlert(
      <Box>
        DSR automation has failed for{" "}
        <Text as="span" fontWeight="semibold">
          {requests.count}
        </Text>{" "}
        privacy request(s). Please review the event log for further details.
      </Box>,
      undefined,
      {
        containerStyle: { maxWidth: "max-content" },
        duration: null,
        id: TOAST_ID,
      },
    );
  };

  return { processing };
};
