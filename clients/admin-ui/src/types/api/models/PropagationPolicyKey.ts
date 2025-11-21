/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Propagation policy keys for propagating a consent choice up or down the hierarchy of notices.
 * Each policy key has its own PropagationPolicy implementation.
 */
export enum PropagationPolicyKey {
  DEFAULT = "default",
  CASCADE_DOWN = "cascade_down",
  CASCADE_UP = "cascade_up",
  CASCADE_UP_AND_DOWN = "cascade_up_and_down",
}
