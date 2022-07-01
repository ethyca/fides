/**
 * Taken from https://redux-toolkit.js.org/rtk-query/usage-with-typescript#inline-error-handling-example
 */

import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import { YAMLException } from "js-yaml";

// generic error of the structure we expect from the Fides backend
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

interface ConflictError {
  data: {
    status: 409;
    detail: {
      error: string;
      resource_type: string;
      fides_key: string;
    };
  };
}

/**
 * Custom type predicate to see if the error has details as returned by the Fides API
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
  error: unknown
): error is ValidationError {
  return (
    typeof error === "object" &&
    error != null &&
    "data" in error &&
    Array.isArray((error as any).data.detail)
  );
}

export function isConflictError(error: unknown): error is ConflictError {
  return (
    typeof error === "object" &&
    error != null &&
    "data" in error &&
    (error as any).status === 409
  );
}

export function isYamlException(error: unknown): error is YAMLException {
  return (
    typeof error === "object" &&
    error != null &&
    "name" in error &&
    (error as any).name === "YAMLException"
  );
}

type RTKReturnType =
  | {
      data: any;
    }
  | {
      error: FetchBaseQueryError | SerializedError;
    };
export function getErrorFromResult(result: RTKReturnType) {
  if ("error" in result) {
    const { error } = result;
    let errorMsg = "An unexpected error occurred. Please try again.";
    if (isErrorWithDetail(error)) {
      errorMsg = error.data.detail;
    } else if (isErrorWithDetailArray(error)) {
      errorMsg = `${error.data.detail[0].msg}: ${error.data.detail[0].loc}`;
    } else if (isConflictError(error)) {
      errorMsg = `${error.data.detail.error} (${error.data.detail.fides_key})`;
    }
    return errorMsg;
  }
  return null;
}
