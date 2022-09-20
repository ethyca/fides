/**
 * The specific error types like these will be codified by a backend change:
 *  https://github.com/ethyca/fides/issues/894
 * Until then, this file contains error models we know the backend might return.
 */
export type { HTTPValidationError, ValidationError } from "~/types/api";

/**
 * This is the base error that any fastapi endpoint can return:
 *  https://fastapi.tiangolo.com/tutorial/handling-errors/#use-httpexception
 */
export interface HTTPException {
  detail?: unknown;
}

/**
 * Some endpoints return a plain string as the detail.
 */
export interface DetailStringError {
  detail: string;
}

/**
 * Source: https://github.com/ethyca/fides/blob/main/src/fidesapi/utils/errors.py#L4
 */
export interface AlreadyExistsError {
  detail: {
    error: string;
    resource_type: string;
    fides_key: string;
  };
}
