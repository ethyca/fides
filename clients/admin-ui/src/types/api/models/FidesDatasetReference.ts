/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Reference to a field from another Collection
 */
export type FidesDatasetReference = {
  dataset: string;
  field: string;
  direction?: FidesDatasetReference.direction;
};

export namespace FidesDatasetReference {
  export enum direction {
    FROM = "from",
    TO = "to",
  }
}
