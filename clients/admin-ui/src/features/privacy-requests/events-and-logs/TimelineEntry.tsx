import {
  Box,
  ErrorWarningIcon,
  Flex,
  GreenCheckCircleIcon,
  Text,
} from "fidesui";
import { PrivacyRequestResults } from "privacy-requests/types";
import React from "react";

import { hasUnresolvedError } from "./helpers";

type TimelineEntryProps = {
  entryKey: string;
  results: PrivacyRequestResults;
};

const TimelineEntry = ({
  entryKey,
  results,
  isLast,
  onViewLog,
}: TimelineEntryProps) => {
  return (
    <Box>
      <Flex alignItems="center" height={23} position="relative">
        <Box zIndex={1}>
          {hasUnresolvedError(results[entryKey]) ? (
            <ErrorWarningIcon />
          ) : (
            <GreenCheckCircleIcon />
          )}
        </Box>
        {!isLast && (
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
          {entryKey}
        </Text>
      </Flex>
      <Text
        cursor="pointer"
        color="complimentary.500"
        fontWeight="500"
        fontSize="sm"
        ml={6}
        mb={7}
        onClick={() => onViewLog(entryKey, results[entryKey])}
      >
        View log
      </Text>
    </Box>
  );
};

export default TimelineEntry;
