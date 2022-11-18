import { Box, Text } from "@fidesui/react";
import { useEffect, useState } from "react";

import { useAlert } from "~/features/common/hooks";

import { useGetAllPrivacyRequestsQuery } from "../privacy-requests.slice";

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
  const TOAST_ID = "dsrErrorAlert";
  const DEFAULT_POLLING_INTERVAL = 15000;
  const STATUS = "error";

  const { data } = useGetAllPrivacyRequestsQuery(
    {
      status: [STATUS],
    },
    { pollingInterval: DEFAULT_POLLING_INTERVAL }
  );

  useEffect(() => {
    const total = data?.total || 0;

    if (total > requests.total) {
      setRequests({ count: total - requests.total, total });
      setHasAlert(true);
    } else {
      setHasAlert(false);
    }
  }, [data?.total, requests.total]);

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
      }
    );
  };

  return { processing };
};
