/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ColumnInfo } from './ColumnInfo';

/**
 * Context information about a database table including its schema, name, and columns.
 */
export type TableContext = {
  schema_name: string;
  table_name: string;
  columns?: Array<ColumnInfo>;
};

