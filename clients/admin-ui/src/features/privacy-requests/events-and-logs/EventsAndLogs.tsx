import { Divider, Flex, Heading } from "fidesui";
import { PrivacyRequestEntity } from "privacy-requests/types";
import React from "react";

import ActivityTimeline from "./ActivityTimeline";

type EventsAndLogsProps = {
  subjectRequest: PrivacyRequestEntity;
};

const EventsAndLogs = ({ subjectRequest }: EventsAndLogsProps) => {
  return (
    <>
      <Heading color="gray.900" fontSize="lg" fontWeight="semibold" mb={4}>
        Events and logs
      </Heading>
      <Divider />
      <Flex mt={3}>
        <ActivityTimeline subjectRequest={subjectRequest} />
      </Flex>
    </>
  );
};

export default EventsAndLogs;
