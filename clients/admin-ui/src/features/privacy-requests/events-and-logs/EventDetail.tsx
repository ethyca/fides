import ClipboardButton from "common/ClipboardButton";
import {
  ChakraBox as Box,
  ChakraDivider as Divider,
  ChakraFlex as Flex,
  ChakraText as Text,
  Tag,
} from "fidesui";
import dynamic from "next/dynamic";
import {
  ExecutionLogStatus,
  ExecutionLogStatusColors,
  ExecutionLogStatusLabels,
} from "privacy-requests/types";
import React from "react";

const MonacoEditor = dynamic(
  () => import("@monaco-editor/react").then((mod) => mod.default),
  { ssr: false },
);

const isJson = (value: string): boolean => {
  try {
    const parsed = JSON.parse(value);
    return parsed !== null && typeof parsed === "object";
  } catch {
    return false;
  }
};

type EventDetailProps = {
  errorMessage: string;
  status?: ExecutionLogStatus;
};

const EventDetail = ({
  errorMessage,
  status = ExecutionLogStatus.ERROR,
}: EventDetailProps) => {
  const showJsonEditor = isJson(errorMessage);

  return (
    <Box height="100%" id="outer">
      <Flex alignItems="center">
        <Text
          size="sm"
          color="gray.700"
          fontWeight="medium"
          marginRight="8px"
          lineHeight="20px"
        >
          Status
        </Text>
        {ExecutionLogStatusLabels[status] ? (
          <Tag color={ExecutionLogStatusColors[status]}>
            {ExecutionLogStatusLabels[status]}
          </Tag>
        ) : (
          <Text size="sm" color="gray.600" fontWeight="medium">
            {status}
          </Text>
        )}
        <Box padding="0px" marginBottom="3px">
          <ClipboardButton copyText={errorMessage} />
        </Box>
      </Flex>
      <Divider marginTop="4px" marginBottom="6px" />
      <Box id="errorWrapper" overflow="auto" height="100%">
        {showJsonEditor ? (
          <MonacoEditor
            language="json"
            value={errorMessage}
            height="100%"
            options={{
              readOnly: true,
              minimap: { enabled: false },
              lineNumbers: "off",
              scrollBeyondLastLine: false,
              wordWrap: "on",
              renderLineHighlight: "none",
              overviewRulerLanes: 0,
              hideCursorInOverviewRuler: true,
              folding: false,
              fontSize: 12,
            }}
          />
        ) : (
          <Text as="pre" whiteSpace="pre-wrap" wordBreak="break-word">
            {errorMessage}
          </Text>
        )}
      </Box>
    </Box>
  );
};

export default EventDetail;
