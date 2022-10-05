import { Box, VStack } from "@fidesui/react";

import { PrivacyRequest } from "../privacy-requests/types";
import EventsAndLogs from "./events-and-logs/EventsAndLogs";
import ManualProcessingList from "./manual-processing/ManualProcessingList";
import RequestDetails from "./RequestDetails";
import SubjectIdentities from "./SubjectIdentities";

type SubjectRequestProps = {
  subjectRequest: PrivacyRequest;
};

const SubjectRequest: React.FC<SubjectRequestProps> = ({ subjectRequest }) => (
  <VStack align="stretch" display="flex-start" spacing={6}>
    <Box>
      <RequestDetails subjectRequest={subjectRequest} />
    </Box>
    <Box>
      <SubjectIdentities subjectRequest={subjectRequest} />
    </Box>
    {subjectRequest.status === "requires_input" && (
      <Box>
        <ManualProcessingList subjectRequest={subjectRequest} />
      </Box>
    )}
    <Box>
      <EventsAndLogs subjectRequest={subjectRequest} />
    </Box>
  </VStack>
);

export default SubjectRequest;
