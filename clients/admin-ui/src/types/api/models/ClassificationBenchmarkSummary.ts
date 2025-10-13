/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AccuracyMetrics } from './AccuracyMetrics';
import type { BenchmarkStatus } from './BenchmarkStatus';

/**
 * Summary results of a classification benchmark.
 */
export type ClassificationBenchmarkSummary = {
  /**
   * Unique identifier for the benchmark
   */
  id: string;
  /**
   * Key of the monitor being evaluated
   */
  monitor_config_key: string;
  /**
   * Fides dataset key used as ground truth
   */
  dataset_fides_key: string;
  /**
   * The staged resource URNs that were evaluated
   */
  resource_urns: Array<string>;
  /**
   * When the benchmark was created
   */
  created_at: string;
  /**
   * Overall accuracy metrics (null for failed benchmarks)
   */
  overall_metrics?: (AccuracyMetrics | null);
  /**
   * Status of the benchmark execution
   */
  status: BenchmarkStatus;
  /**
   * Status messages and error information
   */
  messages: Array<string>;
};

