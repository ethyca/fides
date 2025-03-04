import {
  Box,
  ErrorWarningIcon,
  Flex,
  GreenCheckCircleIcon,
  Text,
  YellowWarningIcon,
} from "fidesui";
import { ExecutionLog } from "privacy-requests/types";
import React from "react";

import { hasSkippedEntry, hasUnresolvedError } from "./helpers";

type TimelineEntryProps = {
  entryKey: string;
  logs: ExecutionLog[];
  isLast: boolean;
  onViewLog: () => void;
};

const getStatusIcon = (logs: ExecutionLog[]) => {
  if (hasUnresolvedError(logs)) {
    return <ErrorWarningIcon />; // Default is red
  }
  if (hasSkippedEntry(logs)) {
    return <YellowWarningIcon />;
  }
  return <GreenCheckCircleIcon />;
};

const TimelineEntry = ({
  entryKey,
  logs,
  isLast,
  onViewLog,
}: TimelineEntryProps) => {
  return (
    <Box>
      <Flex alignItems="center" height={23} position="relative">
        <Box zIndex={1}>{getStatusIcon(logs)}</Box>
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
        onClick={() => onViewLog()}
      >
        View log
      </Text>
    </Box>
  );
};

export default TimelineEntry;
