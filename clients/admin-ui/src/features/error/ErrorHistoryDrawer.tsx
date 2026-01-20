/**
 * ErrorHistoryDrawer - Displays recent API errors for debugging
 *
 * Allows FDEs to view errors that occurred before they connected to
 * a customer's machine. Shows the last N errors with expandable details.
 */

import { Button, Drawer, Empty, Flex, List, Space, Typography } from "fidesui";
import { useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import ClipboardButton from "~/features/common/ClipboardButton";

import {
  clearErrors,
  ErrorLogEntry,
  selectErrorCount,
  selectErrors,
} from "./error.slice";

const { Text } = Typography;

/**
 * Formats a timestamp into a relative time string (e.g., "2 min ago")
 */
const formatRelativeTime = (timestamp: number): string => {
  const now = Date.now();
  const diffMs = now - timestamp;
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);

  if (diffSeconds < 60) {
    return "Just now";
  }
  if (diffMinutes < 60) {
    return `${diffMinutes} min ago`;
  }
  if (diffHours < 24) {
    return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
  }
  return new Date(timestamp).toLocaleString();
};

/**
 * Maximum characters to display in the collapsed raw data preview.
 */
const MAX_PREVIEW_LENGTH = 100;

/**
 * Single error entry item component
 */
const ErrorHistoryItem = ({ error }: { error: ErrorLogEntry }) => {
  const [expanded, setExpanded] = useState(false);

  // Defensive: handle old entries that may not have rawData
  const rawData = error.rawData ?? JSON.stringify(error, null, 2);

  const previewData =
    rawData.length > MAX_PREVIEW_LENGTH
      ? `${rawData.substring(0, MAX_PREVIEW_LENGTH)}...`
      : rawData;

  return (
    <List.Item
      style={{
        display: "block",
        padding: "12px",
        borderBottom: "1px solid #f0f0f0",
      }}
    >
      {/* Header row */}
      <Flex justify="space-between" align="flex-start">
        <Space direction="vertical" size={0}>
          {/* Status and message */}
          <Text>
            {error.status !== undefined && (
              <Text strong style={{ marginRight: 8 }}>
                [{error.status}]
              </Text>
            )}
            {error.message}
          </Text>

          {/* Endpoint and timestamp */}
          <Text type="secondary" style={{ fontSize: 12 }}>
            {error.endpoint} • {formatRelativeTime(error.timestamp)}
          </Text>
        </Space>

        {/* Copy button */}
        <ClipboardButton copyText={rawData} size="small" />
      </Flex>

      {/* Expandable details */}
      <div style={{ marginTop: 8 }}>
        <details
          open={expanded}
          onToggle={(e) => setExpanded((e.target as HTMLDetailsElement).open)}
        >
          <summary
            style={{
              cursor: "pointer",
              fontSize: 12,
              color: "#8c8c8c",
              userSelect: "none",
            }}
          >
            {expanded ? "Hide details" : "Show details"}
          </summary>

          <div
            style={{
              marginTop: 8,
              padding: 8,
              backgroundColor: "#fafafa",
              borderRadius: 4,
              fontSize: 11,
              fontFamily: "monospace",
              maxHeight: 150,
              overflowY: "auto",
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
            }}
          >
            {rawData}
          </div>
        </details>

        {/* Collapsed preview when not expanded */}
        {!expanded && (
          <Text
            type="secondary"
            style={{
              fontSize: 11,
              fontFamily: "monospace",
              display: "block",
              marginTop: 4,
            }}
          >
            {previewData}
          </Text>
        )}
      </div>
    </List.Item>
  );
};

interface ErrorHistoryDrawerProps {
  open: boolean;
  onClose: () => void;
}

/**
 * Drawer component showing the error history list.
 */
const ErrorHistoryDrawer = ({ open, onClose }: ErrorHistoryDrawerProps) => {
  const dispatch = useAppDispatch();
  const errors = useAppSelector(selectErrors);
  const errorCount = useAppSelector(selectErrorCount);

  const handleClearAll = () => {
    dispatch(clearErrors());
  };

  return (
    <Drawer
      open={open}
      onClose={onClose}
      placement="right"
      width={480}
      title={
        <Flex justify="space-between" align="center">
          <span>Error history ({errorCount})</span>
          {errorCount > 0 && (
            <Button size="small" onClick={handleClearAll}>
              Clear all
            </Button>
          )}
        </Flex>
      }
    >
      {errors.length === 0 ? (
        <Empty
          description="No errors recorded"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      ) : (
        <List
          dataSource={errors}
          renderItem={(error) => (
            <ErrorHistoryItem key={error.id} error={error} />
          )}
          split={false}
        />
      )}
    </Drawer>
  );
};

export default ErrorHistoryDrawer;
