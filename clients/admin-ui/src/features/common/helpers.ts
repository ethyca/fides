import { YAMLException } from "js-yaml";
import { narrow } from "narrow-minded";

import {
  isAlreadyExistsErrorData,
  isAPIError,
  isDetailStringErrorData,
  isHTTPValidationErrorData,
  isParsingError,
  RTKErrorResult,
} from "~/types/errors/api";

export { isErrorResult } from "~/types/errors/api";

export const isYamlException = (error: unknown): error is YAMLException =>
  narrow({ name: "string" }, error) && error.name === "YAMLException";

const DEFAULT_ERROR_MESSAGE = "An unexpected error occurred. Please try again.";

export const getErrorMessage = (
  error: RTKErrorResult["error"],
  defaultMsg = DEFAULT_ERROR_MESSAGE
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
  }

  return defaultMsg;
};

export interface ParsedError {
  status: number;
  message: string;
}

export const parseError = (
  error: RTKErrorResult["error"],
  defaultError = {
    status: 500,
    message: DEFAULT_ERROR_MESSAGE,
  }
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
