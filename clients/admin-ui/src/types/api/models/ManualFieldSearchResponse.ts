/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ManualFieldListItem } from "./ManualFieldListItem";
import type { ManualFieldSearchFilterOptions } from "./ManualFieldSearchFilterOptions";

/**
 * Full paginated response returned by the endpoint.
 */
export type ManualFieldSearchResponse = {
  items: Array<ManualFieldListItem>;
  total: number;
  page: number;
  size: number;
  pages: number;
  filter_options: ManualFieldSearchFilterOptions;
};
