import ClipboardButton from "common/ClipboardButton";
import { AntTag as Tag, Box, Divider, Flex, Text } from "fidesui";
import React from "react";

type EventErrorProps = {
  errorMessage: string;
};

const EventError = ({ errorMessage }: EventErrorProps) => (
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
      <Tag color="error">Error</Tag>
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

export default EventError;
