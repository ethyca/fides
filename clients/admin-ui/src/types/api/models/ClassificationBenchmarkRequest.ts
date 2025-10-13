/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Request model for starting a classification benchmark.
 */
export type ClassificationBenchmarkRequest = {
  /**
   * Key of the monitor to evaluate
   */
  monitor_config_key: string;
  /**
   * Fides dataset key to use as ground truth
   */
  dataset_fides_key: string;
  /**
   * The staged resource URNs to evaluate
   */
  resource_urns: Array<string>;
};

