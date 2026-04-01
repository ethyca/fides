/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { BreakdownItem } from "./BreakdownItem";

/**
 * Top N breakdowns of data categories and/or data uses.
 *
 * Both fields are nullable — populate whichever applies to the monitor type.
 * In the future, a single monitor type may populate both.
 */
export type TopClassifications = {
  data_categories?: Array<BreakdownItem> | null;
  data_uses?: Array<BreakdownItem> | null;
};
