/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { TableContext } from "./TableContext";

/**
 * Input for the classification, containing either the content to classify
 * or the fully qualified column name, or both. Can also include table context
 * information to aid in classification decisions.
 */
export type ClassifyInput = {
  fq_column_name?: string | null;
  text?: string | null;
  table_context?: TableContext | null;
};
