import ClipboardButton from "common/ClipboardButton";
import { AntTag as Tag, Box, Divider, Flex, Text } from "fidesui";
import { ExecutionLogStatus } from "privacy-requests/types";
import React from "react";

type EventDetailProps = {
  errorMessage: string;
  status?: ExecutionLogStatus;
};

const getTagColorForStatus = (status?: ExecutionLogStatus) => {
  switch (status) {
    case ExecutionLogStatus.SKIPPED:
      return "warning";
    case ExecutionLogStatus.ERROR:
      return "error";
    default:
      return "error"; // fallback to error
  }
};

const EventDetail = ({
  errorMessage,
  status = ExecutionLogStatus.ERROR,
}: EventDetailProps) => (
  <Box height="100%" id="outer">
    <Flex alignItems="center" paddingBottom="8px">
      <Text
        size="sm"
        color="gray.700"
        fontWeight="medium"
        marginRight="8px"
        lineHeight="20px"
      >
        Status
      </Text>
      <Tag color={getTagColorForStatus(status)}>{status}</Tag>
      <Box padding="0px" marginBottom="3px">
        <ClipboardButton copyText={errorMessage} />
      </Box>
    </Flex>
    <Divider />
    <Box id="errorWrapper" overflow="auto" height="100%">
      <Text>{errorMessage}</Text>
    </Box>
  </Box>
);

export default EventDetail;
