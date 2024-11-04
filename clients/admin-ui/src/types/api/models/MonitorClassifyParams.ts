/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Extension of base ClassifyParams to include some additional
 * classification parameters that can be used with Discovery monitors
 */
export type MonitorClassifyParams = {
  possible_targets?: Array<string> | null;
  top_n?: number;
  remove_stop_words?: boolean;
  pii_threshold?: number;
  num_samples?: number;
  num_threads?: number;
  context_weight?: number;
  content_weight?: number;
  prefer_context?: boolean;
  excluded_categories?: Array<any>;
  language?: string;
  decision_method?: string;
  aggregation_method?: string;
  infer_not_pii?: boolean;
  content_model?: string;
  context_regex_pattern_mapping?: Array<any[]>;
};
