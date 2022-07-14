import { YAMLException } from "js-yaml";
import { narrow } from "narrow-minded";

import {
  isAlreadyExistsErrorData,
  isAPIError,
  isDetailStringErrorData,
  isHTTPValidationErrorData,
  RTKErrorResult,
} from "~/types/errors/api";

export { isErrorResult } from "~/types/errors/api";

export const isYamlException = (error: unknown): error is YAMLException =>
  narrow({ name: "string" }, error) && error.name === "YAMLException";

export const getErrorMessage = (
  error: RTKErrorResult["error"],
  defaultMsg = "An unexpected error occurred. Please try again."
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
