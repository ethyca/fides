import { useEffect, useState } from "react";

import { useGetAllClassifyInstancesQuery } from "~/features/plus/plus.slice";
import { ClassificationStatus, GenerateTypes } from "~/types/api";

const POLL_INTERVAL_SECONDS = 3;

/**
 * Poll for updates to classification until all classifications are finished
 */
export const usePollForClassifications = ({
  resourceType,
  fidesKeys,
  skip,
}: {
  resourceType: GenerateTypes;
  fidesKeys?: string[];
  skip?: boolean;
}) => {
  const [shouldPoll, setShouldPoll] = useState(true);
  const result = useGetAllClassifyInstancesQuery(
    {
      resource_type: resourceType,
      fides_keys: fidesKeys,
    },
    {
      skip,
      pollingInterval: shouldPoll ? POLL_INTERVAL_SECONDS * 1000 : undefined,
    },
  );

  const isClassificationFinished = result.data
    ? result.data.every(
        (c) =>
          c.status === ClassificationStatus.COMPLETE ||
          c.status === ClassificationStatus.FAILED ||
          c.status === ClassificationStatus.REVIEWED,
      )
    : false;

  useEffect(() => {
    if (isClassificationFinished) {
      setShouldPoll(false);
    }
  }, [isClassificationFinished]);

  return { ...result, isClassificationFinished };
};
