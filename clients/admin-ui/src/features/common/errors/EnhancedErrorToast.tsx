/**
 * EnhancedErrorToast - A detailed error toast for debugging
 *
 * This component provides Forward Deployment Engineers with actionable error
 * information directly in the UI, eliminating the need to dig through console logs.
 *
 * Features:
 * - Shows actual error message (not generic text)
 * - Displays endpoint context (e.g., "POST /api/v1/config")
 * - Collapsible details section for raw error data
 * - One-click copy of full error payload
 *
 * IMPORTANT: This component is rendered via createStandaloneToast() which operates
 * OUTSIDE the React tree. Therefore:
 * - DO NOT use React hooks (useState, useEffect, etc.) - they won't work
 * - DO NOT rely on React Context providers
 * - Use native HTML elements for interactivity (details/summary)
 *
 * Usage:
 * This component is rendered by the RTK Query error middleware when
 * `error_notification_mode` is set to "toast" in the application config.
 */

import {
  ChakraAlert as Alert,
  ChakraAlertDescription as AlertDescription,
  ChakraAlertIcon as AlertIcon,
  ChakraBox as Box,
  ChakraCloseButton as CloseButton,
  ChakraText as Text,
} from "fidesui";
import { MouseEventHandler } from "react";

import ClipboardButton from "~/features/common/ClipboardButton";

/**
 * Maximum characters to display in the details section.
 * Full payload is still available via clipboard copy.
 */
const MAX_DISPLAY_LENGTH = 2000;

/**
 * Truncates a string to maxLength and adds indicator if truncated.
 */
const truncateForDisplay = (str: string, maxLength: number): string => {
  if (str.length <= maxLength) {
    return str;
  }
  return `${str.substring(0, maxLength)}\n\n... [truncated - use copy button for full payload]`;
};

/**
 * Props for the EnhancedErrorToast component
 */
export interface EnhancedErrorToastProps {
  /** HTTP status code or error type (e.g., 404, 500, "PARSING_ERROR") */
  status: number | string | undefined;
  /** Human-readable error message parsed from the response */
  message: string;
  /** The API endpoint that failed (e.g., "GET /api/v1/config") */
  endpoint?: string;
  /** JSON string of the full error payload for copying */
  rawData: string;
  /** Callback to close the toast */
  onClose?: MouseEventHandler<HTMLButtonElement>;
}

/**
 * Enhanced error toast with expandable details and copy functionality.
 *
 * Uses native HTML <details>/<summary> for expand/collapse because this
 * component runs outside the React tree (via createStandaloneToast).
 */
const EnhancedErrorToast = ({
  status,
  message,
  endpoint,
  rawData,
  onClose,
}: EnhancedErrorToastProps) => {
  const displayData = truncateForDisplay(rawData, MAX_DISPLAY_LENGTH);

  return (
    <Alert
      alignItems="flex-start"
      status="error"
      data-testid="enhanced-error-toast"
      flexDirection="column"
      maxWidth="500px"
    >
      {/* Header row with icon, message, and close button */}
      <Box display="flex" alignItems="flex-start" width="100%">
        <AlertIcon />
        <Box flex="1">
          <AlertDescription>
            {/* Status badge */}
            {status !== undefined && (
              <Text as="span" fontWeight="bold" marginRight={2}>
                [{status}]
              </Text>
            )}
            {/* Error message */}
            <Text as="span">{message}</Text>
          </AlertDescription>

          {/* Endpoint context if available */}
          {endpoint && (
            <Text fontSize="sm" color="gray.600" marginTop={1}>
              Endpoint: <code>{endpoint}</code>
            </Text>
          )}
        </Box>
        <CloseButton
          onClick={onClose}
          position="relative"
          right={0}
          size="sm"
          top={-1}
        />
      </Box>

      {/*
        Expandable details section using native HTML <details>/<summary>.
        This works in standalone toast context where React hooks don't work.
      */}
      <Box marginTop={2} width="100%">
        <details data-testid="error-details-toggle">
          <summary
            style={{
              cursor: "pointer",
              fontSize: "0.875rem",
              color: "#718096",
              userSelect: "none",
            }}
          >
            Show details
          </summary>

          {/* Details content */}
          <Box
            marginTop={2}
            padding={2}
            backgroundColor="gray.100"
            borderRadius="md"
            fontSize="xs"
            fontFamily="mono"
            maxHeight="150px"
            overflowY="auto"
            position="relative"
          >
            {/* Copy button - copies FULL rawData, not truncated version */}
            <Box position="absolute" top={1} right={1}>
              <ClipboardButton copyText={rawData} size="small" />
            </Box>

            {/* Raw error data (may be truncated for display) */}
            <Text
              as="pre"
              whiteSpace="pre-wrap"
              wordBreak="break-word"
              paddingRight={8}
              margin={0}
            >
              {displayData}
            </Text>
          </Box>
        </details>
      </Box>
    </Alert>
  );
};

export default EnhancedErrorToast;
