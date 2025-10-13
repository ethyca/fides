/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Types of tasks that can be executed by a worker.
 */
export enum MonitorTaskType {
  DETECTION = 'detection',
  CLASSIFICATION = 'classification',
  LLM_CLASSIFICATION = 'llm_classification',
  PROMOTION = 'promotion',
  REMOVAL_PROMOTION = 'removal_promotion',
}
