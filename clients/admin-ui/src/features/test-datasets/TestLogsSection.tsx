import { format } from "date-fns-tz";
import { Box, Heading, HStack, Text } from "fidesui";
import { memo, useCallback, useEffect, useMemo, useRef } from "react";
import { useSelector } from "react-redux";

import { useAppDispatch } from "~/app/hooks";
import ClipboardButton from "~/features/common/ClipboardButton";
import { useGetTestLogsQuery } from "~/features/privacy-requests";

import {
  selectLogs,
  selectPrivacyRequestId,
  setLogs,
} from "./dataset-test.slice";

const formatTimestamp = (isoTimestamp: string) => {
  const date = new Date(isoTimestamp);
  return format(date, "yyyy-MM-dd HH:mm:ss.SSS");
};

const getLevelColor = (level: string) => {
  switch (level) {
    case "ERROR":
      return "red.500";
    case "WARNING":
      return "orange.500";
    case "INFO":
      return "blue.500";
    default:
      return "gray.500";
  }
};

interface LogLineProps {
  log: {
    timestamp: string;
    level: string;
    module_info: string;
    message: string;
  };
}

const LogLine = memo(({ log }: LogLineProps) => (
  <Box
    as="pre"
    margin={0}
    fontSize="xs"
    fontFamily="monospace"
    whiteSpace="pre-wrap"
    wordBreak="break-word"
  >
    <Text as="span" color="green.500">
      {formatTimestamp(log.timestamp)}
    </Text>
    <Text as="span"> | </Text>
    <Text as="span" color={getLevelColor(log.level)}>
      {log.level.padEnd(8)}
    </Text>
    <Text as="span"> | </Text>
    <Text as="span" color="cyan.500">
      {log.module_info}
    </Text>
    <Text as="span"> - </Text>
    <Text
      as="span"
      color={
        log.level === "ERROR" || log.level === "WARNING"
          ? getLevelColor(log.level)
          : "gray.800"
      }
    >
      {log.message}
    </Text>
  </Box>
));

LogLine.displayName = "LogLine";

const TestLogsSection = () => {
  const dispatch = useAppDispatch();
  const logsRef = useRef<HTMLDivElement>(null);
  const privacyRequestId = useSelector(selectPrivacyRequestId);
  const logs = useSelector(selectLogs);

  // Poll for logs when we have a privacy request ID
  const { data: newLogs } = useGetTestLogsQuery(
    { privacy_request_id: privacyRequestId! },
    {
      skip: !privacyRequestId,
      pollingInterval: 1000,
    },
  );

  // Update logs in store when new logs arrive
  useEffect(() => {
    if (newLogs) {
      dispatch(setLogs(newLogs));
    }
  }, [newLogs, dispatch]);

  // Auto scroll to bottom when new logs arrive
  const scrollToBottom = useCallback(() => {
    if (logsRef.current) {
      logsRef.current.scrollTop = logsRef.current.scrollHeight;
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [logs, scrollToBottom]);

  // Format logs for copying to clipboard
  const plainLogs = useMemo(
    () =>
      logs
        ?.map(
          (log) =>
            `${formatTimestamp(log.timestamp)} | ${log.level} | ${log.module_info} - ${log.message}`,
        )
        .join("\n") || "",
    [logs],
  );

  return (
    <>
      <Heading
        as="h3"
        size="sm"
        display="flex"
        alignItems="center"
        justifyContent="space-between"
      >
        <HStack>
          <Text>Test logs</Text>
          <ClipboardButton copyText={plainLogs} />
        </HStack>
      </Heading>
      <Box
        ref={logsRef}
        height="200px"
        overflowY="auto"
        borderWidth={1}
        borderColor="gray.200"
        borderRadius="md"
        p={2}
      >
        {logs?.map((log) => (
          <LogLine
            key={`${log.timestamp}-${log.module_info}-${log.message}`}
            log={log}
          />
        ))}
      </Box>
    </>
  );
};

export default memo(TestLogsSection);
