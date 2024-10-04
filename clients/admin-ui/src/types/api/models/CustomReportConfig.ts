/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import { CustomReportTableState } from "~/features/datamap/types";

/**
 * The configuration for a custom report.
 */
export type CustomReportConfig = {
  /**
   * Flexible dictionary storing UI-specific table state data without a fixed schema
   */
  table_state?: CustomReportTableState;
  /**
   * A map between column keys and custom labels
   */
  column_map?: Record<string, string>;
};
