/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response model for classification benchmark initiation.
 */
export type ClassificationBenchmarkResponse = {
  /**
   * Unique identifier for the benchmark
   */
  benchmark_id: string;
  /**
   * Status of the benchmark
   */
  status: string;
  /**
   * Additional information about the benchmark
   */
  message: string;
};

