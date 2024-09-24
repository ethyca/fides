import { Divider, Flex, Heading } from "fidesui";
import { PrivacyRequestEntity } from "privacy-requests/types";
import React, { useState } from "react";

import ActivityTimeline from "./ActivityTimeline";
import EventDetails, { EventData } from "./EventDetails";

type EventsAndLogsProps = {
  subjectRequest: PrivacyRequestEntity;
};

const EventsAndLogs = ({ subjectRequest }: EventsAndLogsProps) => {
  const [eventData, setEventData] = useState<EventData>();

  return (
    <>
      <Heading color="neutral.900" fontSize="lg" fontWeight="semibold" mb={4}>
        Events and logs
      </Heading>
      <Divider />
      <Flex mt={3}>
        <ActivityTimeline
          subjectRequest={subjectRequest}
          setEventDetails={setEventData}
        />
        <EventDetails eventData={eventData} />
      </Flex>
    </>
  );
};

export default EventsAndLogs;
