/* istanbul ignore file */
/* tslint:disable */

/**
 * Collection-level specific annotations used for query traversal
 */
export type CollectionMeta = {
  after?: Array<string> | null;
  skip_processing?: boolean | null;
};
