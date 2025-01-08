import { Box, VStack } from "fidesui";
import { useMemo } from "react";

import { useGetAllPrivacyRequestsQuery } from "~/features/privacy-requests";
import { PrivacyRequestStatus } from "~/types/api";

import EventsAndLogs from "./events-and-logs/EventsAndLogs";
import ManualProcessingList from "./manual-processing/ManualProcessingList";
import RequestDetails from "./RequestDetails";
import SubjectIdentities from "./SubjectIdentities";
import { PrivacyRequestEntity } from "./types";

type PrivacyRequestProps = {
  data: PrivacyRequestEntity;
};

const PrivacyRequest = ({ data: initialData }: PrivacyRequestProps) => {
  const queryOptions = useMemo(
    () => ({
      id: initialData.id,
      verbose: true,
    }),
    [initialData.id],
  );

  // Poll for the latest privacy request data while the status is approved or in processing
  const { data: latestData } = useGetAllPrivacyRequestsQuery(queryOptions, {
    pollingInterval:
      initialData.status === PrivacyRequestStatus.APPROVED ||
      initialData.status === PrivacyRequestStatus.IN_PROCESSING
        ? 2000
        : 0,
    skip: !initialData.id,
  });

  // Use latest data if available, otherwise use initial data
  const subjectRequest = latestData?.items[0] ?? initialData;

  return (
    <VStack align="stretch" display="flex-start" spacing={6}>
      <Box data-testid="privacy-request-details">
        <RequestDetails subjectRequest={subjectRequest} />
      </Box>
      <Box>
        <SubjectIdentities subjectRequest={subjectRequest} />
      </Box>
      {subjectRequest.status === PrivacyRequestStatus.REQUIRES_INPUT && (
        <Box>
          <ManualProcessingList subjectRequest={subjectRequest} />
        </Box>
      )}
      <Box>
        <EventsAndLogs subjectRequest={subjectRequest} />
      </Box>
    </VStack>
  );
};

export default PrivacyRequest;
