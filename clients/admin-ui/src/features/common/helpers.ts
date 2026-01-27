/**
 * Taken from https://redux-toolkit.js.org/rtk-query/usage-with-typescript#inline-error-handling-example
 */
import { FetchBaseQueryError } from "@reduxjs/toolkit/query";

import {
  isAlreadyExistsErrorData,
  isAPIError,
  isDetailStringErrorData,
  isHTTPValidationErrorData,
  isNotFoundError,
  isParsingError,
  RTKErrorResult,
} from "~/types/errors/api";

export { isErrorResult } from "~/types/errors/api";

const DEFAULT_ERROR_MESSAGE = "An unexpected error occurred. Please try again.";

export const getErrorMessage = (
  error: RTKErrorResult["error"],
  defaultMsg = DEFAULT_ERROR_MESSAGE,
) => {
  if (isAPIError(error)) {
    if (isDetailStringErrorData(error.data)) {
      return error.data.detail;
    }
    if (isHTTPValidationErrorData(error.data)) {
      const firstError = error.data.detail?.[0];
      return `${firstError?.msg}: ${firstError?.loc}`;
    }
    if (error.status === 409 && isAlreadyExistsErrorData(error.data)) {
      return `${error.data.detail.error} (${error.data.detail.fides_key})`;
    }
    if (error.status === 404 && isNotFoundError(error.data)) {
      return `${error.data.detail.error} (${error.data.detail.fides_key})`;
    }
  }

  return defaultMsg;
};

/**
 * Type predicate to narrow an unknown error to `FetchBaseQueryError`
 */
export function isFetchBaseQueryError(
  error: unknown,
): error is FetchBaseQueryError {
  return typeof error === "object" && error !== null && "status" in error;
}

/**
 * Type predicate to narrow an unknown error to an object with a string 'message' property
 */
export function isErrorWithMessage(
  error: unknown,
): error is { message: string } {
  return (
    typeof error === "object" &&
    error !== null &&
    "message" in error &&
    typeof (error as any).message === "string"
  );
}

// generic error of the structure we expect from the Fidesops backend
interface ResponseError {
  data: {
    detail: string;
  };
}

interface ErrorDetail {
  loc: string[];
  msg: string;
  type: string;
}

interface ValidationError {
  data: {
    detail: ErrorDetail[];
  };
}

/**
 * Custom type predicate to see if the error has details as returned by the Fidesops API
 * @param error
 * @returns
 */
export function isErrorWithDetail(error: unknown): error is ResponseError {
  return (
    typeof error === "object" &&
    error !== null &&
    "data" in error &&
    (error as any).data !== null &&
    typeof (error as any).data.detail === "string"
  );
}

export function isErrorWithDetailArray(
  error: unknown,
): error is ValidationError {
  return (
    typeof error === "object" &&
    error !== null &&
    "data" in error &&
    (error as any).data !== null &&
    Array.isArray((error as any).data.detail)
  );
}

export interface ParsedError {
  status: number;
  message: string;
}

export const parseError = (
  error: RTKErrorResult["error"],
  defaultError = {
    status: 500,
    message: DEFAULT_ERROR_MESSAGE,
  },
): ParsedError => {
  if (isParsingError(error)) {
    // This case is known to come up for Internal Server Errors which cannot be parsed as JSON.
    // Ticket #892 will fix the ones produced by the generate endpoint.
    return {
      status: error.originalStatus,
      message: error.data,
    };
  }

  if (isAPIError(error)) {
    const { status } = error;

    return {
      status,
      message: getErrorMessage(error, defaultError.message),
    };
  }

  return defaultError;
};

/**
 * Given an enumeration, create options out of its key and values
 */
export const enumToOptions = (e: { [s: number]: string }) =>
  Object.entries(e).map((entry) => ({
    value: entry[1],
    label: entry[1],
  }));

export enum VendorSources {
  GVL = "gvl",
  AC = "gacp",

  // this is just a generic placeholder/fallback for now
  // TODO: update this to a proper vendor source once we've
  // finalized what we are labeling non-GVL/AC compass vendors
  COMPASS = "compass",
}

export const vendorSourceLabels = {
  [VendorSources.GVL]: {
    label: "GVL",
    fullName: "Global Vendor List",
  },
  [VendorSources.AC]: {
    label: "AC",
    fullName: "Google Additional Consent List",
  },
  // this is just a generic placeholder/fallback for now
  // TODO: update this to a proper vendor source once we've
  // finalized what we are labeling non-GVL/AC compass vendors
  [VendorSources.COMPASS]: {
    label: "",
    fullName: "",
  },
};

export const extractVendorSource = (vendorId: string) => {
  const source = vendorId.split(".")[0];
  if (source === VendorSources.AC) {
    return VendorSources.AC;
  }
  if (source === VendorSources.GVL) {
    return VendorSources.GVL;
  }
  return VendorSources.COMPASS;
};

/**
 * ============================================================================
 * RTK Query Error Action Parsing Utilities
 * ============================================================================
 * @TODO: Cleanup AI generated code and comments.
 * These utilities parse rejected RTK Query actions to extract error information
 * for display in the EnhancedErrorToast component.
 *
 * IMPORTANT: The action structure is based on RTK Query v2.x internals.
 * If RTK Query updates its internal structure, these may need adjustment.
 *
 * Expected action structure:
 * {
 *   type: "baseApi/executeQuery/rejected",
 *   payload: { status: 404, data: {...} },    // The error response
 *   meta: {
 *     arg: {
 *       endpointName: "getPrivacyRequest",    // API endpoint name
 *       originalArgs: { id: "123" }           // Original request args
 *     },
 *     baseQueryMeta: {
 *       request: { url: "/api/v1/..." }       // Fallback for URL
 *     }
 *   },
 *   error: { message: "Rejected" }            // RTK error wrapper
 * }
 */

/**
 * Props returned by parseRTKErrorAction, matching EnhancedErrorToastProps
 */
export interface ParsedRTKError {
  /** HTTP status code or error type (e.g., 404, 500, "PARSING_ERROR") */
  status: number | string | undefined;
  /** Human-readable error message */
  message: string;
  /** The API endpoint that failed (e.g., "getPrivacyRequest") */
  endpoint: string;
  /** JSON string of the full error payload for copying */
  rawData: string;
}

/**
 * Safely extracts the endpoint name from an RTK Query rejected action.
 *
 * @param action - The rejected RTK Query action
 * @returns The endpoint name or "Unknown endpoint" if extraction fails
 */
const extractEndpointName = (action: unknown): string => {
  try {
    if (
      typeof action === "object" &&
      action !== null &&
      "meta" in action &&
      typeof (action as any).meta === "object" &&
      (action as any).meta !== null &&
      "arg" in (action as any).meta &&
      typeof (action as any).meta.arg === "object" &&
      (action as any).meta.arg !== null &&
      "endpointName" in (action as any).meta.arg &&
      typeof (action as any).meta.arg.endpointName === "string"
    ) {
      return (action as any).meta.arg.endpointName;
    }
  } catch {
    // Fail silently - structure may have changed
  }
  return "Unknown endpoint";
};

/**
 * Safely extracts the error status from an RTK Query rejected action.
 *
 * @param action - The rejected RTK Query action
 * @returns The status code/string or undefined if not found
 */
const extractErrorStatus = (action: unknown): number | string | undefined => {
  try {
    if (
      typeof action === "object" &&
      action !== null &&
      "payload" in action &&
      typeof (action as any).payload === "object" &&
      (action as any).payload !== null &&
      "status" in (action as any).payload
    ) {
      return (action as any).payload.status;
    }
  } catch {
    // Fail silently
  }
  return undefined;
};

/**
 * Safely extracts the error payload from an RTK Query rejected action.
 *
 * @param action - The rejected RTK Query action
 * @returns The error payload or the action itself as fallback
 */
const extractErrorPayload = (action: unknown): unknown => {
  try {
    if (
      typeof action === "object" &&
      action !== null &&
      "payload" in action &&
      (action as any).payload !== null
    ) {
      return (action as any).payload;
    }
  } catch {
    // Fail silently
  }
  return action;
};

/**
 * Parses a rejected RTK Query action into props for EnhancedErrorToast.
 *
 * This function safely extracts error information from RTK Query rejected actions,
 * handling malformed or unexpected action structures gracefully.
 *
 * @param action - The rejected RTK Query action (from isRejectedWithValue)
 * @returns Parsed error data ready for EnhancedErrorToast
 *
 * @example
 * ```typescript
 * if (isRejectedWithValue(action)) {
 *   const errorProps = parseRTKErrorAction(action);
 *   // { status: 404, message: "Not found", endpoint: "getUser", rawData: "..." }
 * }
 * ```
 */
export const parseRTKErrorAction = (action: unknown): ParsedRTKError => {
  const endpoint = extractEndpointName(action);
  const status = extractErrorStatus(action);
  const payload = extractErrorPayload(action);

  // Use existing getErrorMessage if we have a proper error payload
  let message = DEFAULT_ERROR_MESSAGE;
  if (isFetchBaseQueryError(payload)) {
    message = getErrorMessage(payload);
  }

  // Format raw data for clipboard - include full action for debugging
  let rawData: string;
  try {
    rawData = JSON.stringify(action, null, 2);
  } catch {
    rawData = String(action);
  }

  return {
    status,
    message,
    endpoint,
    rawData,
  };
};
