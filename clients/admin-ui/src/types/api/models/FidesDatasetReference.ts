/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { EdgeDirection } from "./EdgeDirection";

/**
 * Reference to a field from another Collection
 */
export type FidesDatasetReference = {
  dataset: string;
  field: string;
  direction?: EdgeDirection | null;
};
