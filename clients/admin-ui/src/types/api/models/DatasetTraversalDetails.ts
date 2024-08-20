/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Describes whether or not the parent dataset is traversable; if not, includes
 * an error message describing the traversal issues.
 */
export type DatasetTraversalDetails = {
  is_traversable: boolean;
  msg: string | null;
};
