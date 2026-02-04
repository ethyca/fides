/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Propagation policy keys for propagating a consent choice up or down the hierarchy of notices.
 * Each policy key has its own PropagationPolicy implementation.
 */
export enum PropagationPolicyKey {
  CASCADE_DOWN_OPT_OUT = "cascade_down_opt_out",
  CASCADE_DOWN_ALL = "cascade_down_all",
  CASCADE_UP_ALL = "cascade_up_all",
  CASCADE_UP_ALL_CASCADE_DOWN_ALL = "cascade_up_all_cascade_down_all",
  CASCADE_DOWN_ALL_CASCADE_UP_OPT_IN = "cascade_down_all_cascade_up_opt_in",
}
