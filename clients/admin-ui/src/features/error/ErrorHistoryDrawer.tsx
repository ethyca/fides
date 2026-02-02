/**
 * ErrorHistoryDrawer - Displays recent API errors for debugging
 *
 * Allows FDEs to view errors that occurred before they connected to
 * a customer's machine. Shows the last N errors with expandable details.
 *
 * Features:
 * - View error history with status, message, endpoint
 * - Expand to see full error details
 * - Copy error data to clipboard
 * - Download error report bundle (JSON)
 */

import {
  Alert,
  Button,
  Drawer,
  Empty,
  Flex,
  Icons,
  List,
  Tag,
  Tooltip,
  Typography,
  useMessage,
} from "fidesui";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { downloadErrorReport } from "~/features/common/utils/errorReportUtils";

import {
  clearErrors,
  ErrorLogEntry,
  selectErrorCount,
  selectErrors,
} from "./error.slice";
import { getErrorSuggestions } from "./errorSuggestions";

const { Text, Paragraph } = Typography;

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

interface ErrorHistoryItemProps {
  error: ErrorLogEntry;
  onDownloadReport: (error: ErrorLogEntry) => void;
}

/**
 * Single error entry item component
 */
const ErrorHistoryItem = ({
  error,
  onDownloadReport,
}: ErrorHistoryItemProps) => {
  const suggestions = getErrorSuggestions(error.status);

  return (
    <List.Item
      style={{
        display: "block",
        padding: "12px",
        borderBottom: "1px solid #f0f0f0",
      }}
    >
      <List.Item.Meta
        title={
          <div>
            <Flex className="grow">
              {error.status !== undefined && (
                <>
                  <Tag color="error" style={{ marginRight: 8 }}>
                    {error.status}
                  </Tag>
                  <Text className="flex-1">
                    {JSON.parse(error.rawData)?.type}
                  </Text>
                  <Text
                    type="secondary"
                    style={{ fontSize: 12 }}
                    className="self-end"
                  >
                    {formatRelativeTime(error.timestamp)}
                  </Text>
                </>
              )}
            </Flex>
          </div>
        }
        description={
          <div>
            <Paragraph
              copyable={{
                text: error.rawData,
              }}
            >
              {/* Status and message */}
              {error.message}
            </Paragraph>
            <Tooltip title="Download error report" className="inline">
              <Button
                size="small"
                type="text"
                icon={<Icons.Download />}
                onClick={() => onDownloadReport(error)}
                data-testid="download-report-btn"
              />
            </Tooltip>
          </div>
        }
      />

      {/* Suggestions for this error - collapsible */}
      {suggestions && (
        <details style={{ marginTop: 8 }}>
          <summary
            style={{
              cursor: "pointer",
              fontSize: 12,
              color: "#1890ff",
              userSelect: "none",
              display: "flex",
              alignItems: "center",
              gap: 4,
            }}
          >
            <Icons.Idea size={14} />
            View suggestions
          </summary>
          <Alert
            type="info"
            style={{ marginTop: 8 }}
            message={
              <Space direction="vertical" size={4}>
                <Text strong style={{ fontSize: 12 }}>
                  {suggestions.title}
                </Text>
                <ul style={{ margin: 0, paddingLeft: 16, fontSize: 12 }}>
                  {suggestions.suggestions.map((suggestion) => (
                    <li key={suggestion}>{suggestion}</li>
                  ))}
                </ul>
                {suggestions.docLink && (
                  <a
                    href={suggestions.docLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ fontSize: 12 }}
                  >
                    View documentation →
                  </a>
                )}
              </Space>
            }
          />
        </details>
      )}
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
  const messageApi = useMessage();

  const handleClearAll = () => {
    dispatch(clearErrors());
  };

  const handleDownloadReport = (error: ErrorLogEntry) => {
    downloadErrorReport({
      status: error.status,
      message: error.message,
      endpoint: error.endpoint,
      rawData: error.rawData ?? "",
      timestamp: error.timestamp,
    });
    messageApi.success("Error report downloaded");
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
        </Flex>
      }
      footer={
        <Button
          size="small"
          onClick={handleClearAll}
          type="primary"
          disabled={errorCount <= 0}
        >
          Clear all
        </Button>
      }
    >
      {errors.length === 0 ? (
        <Empty
          description="No errors recorded"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      ) : (
        <List
          dataSource={errors.filter((error) => error.status !== 404)}
          renderItem={(error) => (
            <ErrorHistoryItem
              key={error.id}
              error={error}
              onDownloadReport={handleDownloadReport}
            />
          )}
          split={false}
        />
      )}
    </Drawer>
  );
};

export default ErrorHistoryDrawer;
