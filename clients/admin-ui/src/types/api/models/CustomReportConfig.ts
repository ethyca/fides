/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The configuration for a custom report.
 */
export type CustomReportConfig = {
  /**
   * Flexible dictionary storing UI-specific table state data without a fixed schema
   */
  table_state?: any;
  /**
   * A map between column keys and custom labels
   */
  column_map?: Record<string, any>;
};
