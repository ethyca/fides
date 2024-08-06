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
  return typeof error === "object" && error != null && "status" in error;
}

/**
 * Type predicate to narrow an unknown error to an object with a string 'message' property
 */
export function isErrorWithMessage(
  error: unknown,
): error is { message: string } {
  return (
    typeof error === "object" &&
    error != null &&
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
    error != null &&
    "data" in error &&
    typeof (error as any).data.detail === "string"
  );
}

export function isErrorWithDetailArray(
  error: unknown,
): error is ValidationError {
  return (
    typeof error === "object" &&
    error != null &&
    "data" in error &&
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
