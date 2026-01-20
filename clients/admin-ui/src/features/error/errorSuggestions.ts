/**
 * Error Suggestions Map
 *
 * Provides contextual suggestions for common API errors to help FDEs
 * quickly diagnose and resolve issues.
 */

export interface ErrorSuggestion {
  title: string;
  suggestions: string[];
  docLink?: string;
}

type StatusKey = number | string;

/**
 * Maps error status codes to helpful suggestions.
 *
 * Based on patterns found in codebase:
 * - 403 on AWS scanner (ScannerError.tsx)
 * - 404 on resource lookup (helpers.ts)
 * - 409 already exists (helpers.ts)
 * - PARSING_ERROR from RTK Query (api.ts)
 */
export const ERROR_SUGGESTIONS: Record<StatusKey, ErrorSuggestion> = {
  // === HTTP Status Codes ===

  400: {
    title: "Bad Request",
    suggestions: [
      "Check if request payload matches expected format",
      "Verify required fields are not missing",
      "Look for validation errors in the response details",
    ],
  },

  401: {
    title: "Unauthorized",
    suggestions: [
      "Session may have expired - try logging out and back in",
      "Check if API token is valid and not expired",
      "Verify authentication credentials",
    ],
  },

  403: {
    title: "Forbidden",
    suggestions: [
      "User may lack required permissions for this action",
      "Check role-based access control (RBAC) settings",
      "For AWS operations: verify IAM permissions are configured",
      "Contact admin to verify user permissions",
    ],
    docLink: "https://docs.ethyca.com/fides/configuration",
  },

  404: {
    title: "Not Found",
    suggestions: [
      "Resource may have been deleted or never existed",
      "Check if the fides_key or ID is correct",
      "Verify the API endpoint URL is correct",
      "Resource may not be synced yet - try refreshing",
    ],
  },

  409: {
    title: "Conflict",
    suggestions: [
      "A resource with this fides_key already exists",
      "Use a unique identifier or update the existing resource",
      "Check for duplicate entries in your configuration",
    ],
  },

  422: {
    title: "Validation Error",
    suggestions: [
      "Input data failed validation - check field requirements",
      "Review the error details for specific field issues",
      "Ensure data types match expected formats",
    ],
  },

  500: {
    title: "Internal Server Error",
    suggestions: [
      "Server encountered an unexpected error",
      "Check backend logs for stack trace",
      "Try again - may be a temporary issue",
      "If persistent, report to engineering with error details",
    ],
  },

  502: {
    title: "Bad Gateway",
    suggestions: [
      "Backend server may be down or restarting",
      "Check if all Fides services are running",
      "Verify network connectivity to backend",
    ],
  },

  503: {
    title: "Service Unavailable",
    suggestions: [
      "Service is temporarily overloaded or under maintenance",
      "Wait a moment and retry",
      "Check service health status",
    ],
  },

  504: {
    title: "Gateway Timeout",
    suggestions: [
      "Request took too long to complete",
      "Backend may be processing a large operation",
      "Try with smaller batch sizes if applicable",
    ],
  },

  // === RTK Query Special Statuses ===

  PARSING_ERROR: {
    title: "Response Parsing Error",
    suggestions: [
      "Server returned non-JSON response (possibly HTML error page)",
      "Backend may have crashed - check server logs",
      "Could indicate 500 error that couldn't be parsed",
    ],
  },

  FETCH_ERROR: {
    title: "Network Request Failed",
    suggestions: [
      "Check network connectivity",
      "Backend server may be unreachable",
      "Verify CORS settings if cross-origin",
      "Check if VPN is connected (if required)",
    ],
  },

  TIMEOUT_ERROR: {
    title: "Request Timeout",
    suggestions: [
      "Server took too long to respond",
      "Try again with smaller data payload",
      "Check backend performance/load",
    ],
  },
};

/**
 * Get suggestions for an error status.
 * Returns undefined if no suggestions available.
 */
export const getErrorSuggestions = (
  status: number | string | undefined,
): ErrorSuggestion | undefined => {
  if (status === undefined) {
    return undefined;
  }
  return ERROR_SUGGESTIONS[status];
};
