/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Allows you to partition data based on time ranges using various
 * time expressions and intervals.
 */
export type TimeBasedPartitioning = {
  /**
   * Column name to partition on (e.g., `created_at`, `updated_at`)
   */
  field: string;
  /**
   * Start time expression. Supported formats: `NOW()`, `TODAY()`, `TIMESTAMP(TODAY())`, `YYYY-MM-DD`, `YYYY-MM-DD HH:MM:SS`, or arithmetic expressions like `NOW() - 30 DAYS`, `TIMESTAMP(TODAY() - 30 DAYS)`.
   */
  start?: string | null;
  /**
   * End time expression. Same formats as start field.
   */
  end?: string | null;
  /**
   * Interval expression defining the size of each partition in `DAY(S)`, `WEEK(S)`, `MONTH(S)`, or `YEAR(S)`.
   */
  interval?: string | null;
};
