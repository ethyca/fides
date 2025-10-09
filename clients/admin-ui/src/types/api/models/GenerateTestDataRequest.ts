/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DiffStatusDistribution } from "./DiffStatusDistribution";

/**
 * Request body for generating test staged resources.
 *
 * Extends TestMonitorParams with additional fields for diff status distribution
 * and database naming.
 */
export type GenerateTestDataRequest = {
  /**
   * Regex pattern to identify sharded tables
   */
  sharded_table_pattern?: string | null;
  /**
   * Number of databases to generate
   */
  num_databases?: number;
  /**
   * Number of schemas to generate per database
   */
  num_schemas_per_db?: number;
  /**
   * Number of tables to generate per schema
   */
  num_tables_per_schema?: number;
  /**
   * Number of fields to generate per table
   */
  num_fields_per_table?: number;
  /**
   * Sample data to return for field sampling
   */
  field_sample_data?: Array<string>;
  /**
   * Maximum depth of nested fields
   */
  max_nesting_level?: number;
  /**
   * Percentage of fields that should be nested (0.0 to 1.0)
   */
  nested_field_percentage?: number;
  /**
   * Number of fields to generate for each nested field
   */
  num_fields_per_nested?: number;
  /**
   * Whether to simulate classification when calling the /classify endpoint
   */
  simulate_classification?: boolean;
  /**
   * Optional base name prefix for generated databases
   */
  db_base_name?: string;
  /**
   * Distribution of diff statuses across generated tables. Default: 50% ADDITION, 0% CLASSIFYING, 50% CLASSIFICATION_ADDITION
   */
  diff_status_distribution?: DiffStatusDistribution;
};
