import { format } from "date-fns-tz";
import { Card, Flex, Typography } from "fidesui";
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
      return "var(--ant-color-error)";
    case "WARNING":
      return "var(--ant-color-warning)";
    case "INFO":
      return "var(--ant-color-info)";
    default:
      return "var(--ant-color-text-secondary)";
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
  <pre
    style={{
      margin: 0,
      fontSize: "12px",
      fontFamily: "monospace",
      whiteSpace: "pre-wrap",
      wordBreak: "break-word",
    }}
  >
    <span style={{ color: "var(--ant-color-success)" }}>
      {formatTimestamp(log.timestamp)}
    </span>
    <span> | </span>
    <span style={{ color: getLevelColor(log.level) }}>
      {log.level.padEnd(8)}
    </span>
    <span> | </span>
    <span style={{ color: "var(--ant-color-link)" }}>{log.module_info}</span>
    <span> - </span>
    <span
      style={{
        color:
          log.level === "ERROR" || log.level === "WARNING"
            ? getLevelColor(log.level)
            : "var(--ant-color-text)",
      }}
    >
      {log.message}
    </span>
  </pre>
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
      <Flex align="center" justify="space-between">
        <Flex align="center" gap="small">
          <Typography.Title level={3}>Test logs</Typography.Title>
          <ClipboardButton copyText={plainLogs} />
        </Flex>
      </Flex>
      <Card
        ref={logsRef}
        styles={{
          body: {
            height: "200px",
            overflowY: "auto",
          },
        }}
      >
        {logs?.map((log) => (
          <LogLine
            key={`${log.timestamp}-${log.module_info}-${log.message}`}
            log={log}
          />
        ))}
      </Card>
    </>
  );
};

export default memo(TestLogsSection);
