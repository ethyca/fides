/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Represents an identity value with a label in API responses.
 *
 * The value field accepts MultiValue types which match what LabeledIdentity supports:
 * - int
 * - str
 * - List[Union[int, str]]
 *
 * This allows the schema to accept list values that were previously causing
 * validation errors.
 */
export type IdentityValue = {
  label: string;
  value?: number | string | null;
};
