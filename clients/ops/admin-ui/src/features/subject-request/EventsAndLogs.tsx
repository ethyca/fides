import { Divider, Flex, Heading } from "@fidesui/react";
import React, { useState } from "react";

import { ExecutionLog, PrivacyRequest } from "../privacy-requests/types";
import ActivityTimeline from "./ActivityTimeline";
import EventDetails from "./EventDetails";

type EventsAndLogsProps = {
  subjectRequest: PrivacyRequest;
};

const EventsAndLogs = ({ subjectRequest }: EventsAndLogsProps) => {
  const [eventDetails, setEventDetails] = useState<null | ExecutionLog[]>(null);

  return (
    <>
      <Heading fontSize="lg" fontWeight="semibold" mb={4}>
        Events and logs
      </Heading>
      <Divider />
      <Flex mt={3}>
        <ActivityTimeline
          subjectRequest={subjectRequest}
          setEventDetails={setEventDetails}
        />
        {eventDetails ? <EventDetails eventDetails={eventDetails} /> : null}
      </Flex>
    </>
  );
};

export default EventsAndLogs;
