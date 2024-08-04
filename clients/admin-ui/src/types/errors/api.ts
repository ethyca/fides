import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query";
import { narrow } from "narrow-minded";

import {
  AlreadyExistsError,
  DetailStringError,
  HTTPException,
  HTTPValidationError,
  NotFoundError,
} from "./models";

/**
 * From Redux Toolkit on query error types:
 *  https://redux-toolkit.js.org/rtk-query/usage-with-typescript#inline-error-handling-example
 */
export interface RTKErrorResult {
  error: FetchBaseQueryError | SerializedError;
}

export type RTKResult = { data: unknown } | RTKErrorResult;

/**
 * Use this predicate on an RTK query result to find out if the request returned an error.
 */
export const isErrorResult = (result: RTKResult): result is RTKErrorResult =>
  "error" in result;

/**
 * Use this predicate on the `error` property of an RTK query result to find out if the request
 * returned an error that could not be parsed as JSON. For example, a 500 "Internal Server Error".
 */
export const isParsingError = (
  error: RTKErrorResult["error"],
): error is FetchBaseQueryError & { status: "PARSING_ERROR" } =>
  narrow(
    {
      status: "string",
    },
    error,
  ) && error.status === "PARSING_ERROR";

/**
 * This type is more specific than RTK's FetchBaseQueryError:
 *  - The status must be a number (HTTP code) and not one of RTK's special strings.
 *  - It must contain a `data` object, which will (probably) contain a `detail` property.
 */
export interface APIError {
  status: number;
  data: HTTPException;
}

/**
 * Use this predicate on the `error` property of an RTK query result to find out if the error is one
 * of the types we expect the backend to return.
 */
export const isAPIError = (error: RTKErrorResult["error"]): error is APIError =>
  narrow(
    {
      status: "number",
      data: {},
    },
    error,
  );

/**
 * Use these predicates on the `data` property of an APIError.
 */

export const isDetailStringErrorData = (
  data: unknown,
): data is DetailStringError =>
  narrow(
    {
      detail: "string",
    },
    data,
  );

export const isAlreadyExistsErrorData = (
  data: unknown,
): data is AlreadyExistsError =>
  narrow(
    {
      detail: {
        error: "string",
        resource_type: "string",
        fides_key: "string",
      },
    },
    data,
  );

export const isNotFoundError = (data: unknown): data is NotFoundError =>
  narrow(
    {
      detail: {
        error: "string",
        resource_type: "string",
        fides_key: "string",
      },
    },
    data,
  );

export const isHTTPValidationErrorData = (
  data: unknown,
): data is HTTPValidationError =>
  narrow(
    {
      detail: [
        {
          loc: ["string", "number"],
          msg: "string",
          type: "string",
        },
      ],
    },
    data,
  );
