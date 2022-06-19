/**
 * Taken from https://redux-toolkit.js.org/rtk-query/usage-with-typescript#inline-error-handling-example
 */

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
