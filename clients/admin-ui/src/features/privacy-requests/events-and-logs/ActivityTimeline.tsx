import {
  Box,
  ErrorWarningIcon,
  Flex,
  GreenCheckCircleIcon,
  Text,
} from "fidesui";
import { ExecutionLog, PrivacyRequestEntity } from "privacy-requests/types";
import React from "react";

import { ExecutionLogStatus } from "~/types/api";

import { EventData } from "./EventDetails";

type ActivityTimelineProps = {
  subjectRequest: PrivacyRequestEntity;
  setEventDetails: (d: EventData) => void;
};

const hasUnresolvedError = (entries: ExecutionLog[]) => {
  const groupedByCollection: {
    [key: string]: ExecutionLog;
  } = {};

  // Group the entries by collection_name and keep only the latest entry for each collection.
  entries.forEach((entry) => {
    const { collection_name: collectionName, updated_at: updatedAt } = entry;
    if (
      !groupedByCollection[collectionName] ||
      new Date(groupedByCollection[collectionName].updated_at) <
        new Date(updatedAt)
    ) {
      groupedByCollection[collectionName] = entry;
    }
  });

  // Check if any of the latest entries for the collections have an error status.
  return Object.values(groupedByCollection).some(
    (entry) => entry.status === ExecutionLogStatus.ERROR,
  );
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
          {hasUnresolvedError(results![key]) ? (
            <ErrorWarningIcon />
          ) : (
            <GreenCheckCircleIcon />
          )}
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
        Activity timeline
      </Text>
      {timelineEntries}
    </Box>
  );
};

export default ActivityTimeline;
