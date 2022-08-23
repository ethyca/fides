import { Box, Flex, Text } from "@fidesui/react";
import { GreenCheckCircle } from "common/Icon";
import { PrivacyRequest } from "privacy-requests/types";
import React from "react";

import { EventData } from "./EventDetails";

type ActivityTimelineProps = {
  subjectRequest: PrivacyRequest;
  setEventDetails: (d: EventData) => void;
};

const ActivityTimeline = ({
  subjectRequest,
  setEventDetails,
}: ActivityTimelineProps) => {
  const { results } = subjectRequest;

  const resultKeys = results ? Object.keys(results) : [];

  const timelineEntries = resultKeys.map((key, index) => (
    <Box key={key}>
      <Flex alignItems="center" height={23} position="relative">
        <Box zIndex={1}>
          <GreenCheckCircle />
        </Box>
        {index === resultKeys.length - 1 ? null : (
          <Box
            width="2px"
            height="63px"
            backgroundColor="gray.700"
            position="absolute"
            top="16px"
            left="6px"
            zIndex={0}
          />
        )}

        <Text color="gray.600" fontWeight="500" fontSize="sm" ml={2}>
          {key}
        </Text>
      </Flex>
      <Text
        cursor="pointer"
        color="complimentary.500"
        fontWeight="500"
        fontSize="sm"
        ml={6}
        mb={7}
        onClick={() => {
          setEventDetails({
            key,
            logs: results![key],
          });
        }}
      >
        View Details
      </Text>
    </Box>
  ));

  return (
    <Box width="100%">
      <Text color="gray.900" fontSize="md" fontWeight="500" mb={1}>
        Activity Timeline
      </Text>
      {timelineEntries}
    </Box>
  );
};

export default ActivityTimeline;
