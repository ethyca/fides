/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response model for confirm operations on staged resources
 */
export type ConfirmResourcesResponse = {
  classify_instances?: Array<Record<string, string>>;
  classification_task_id?: string | null;
  removal_promotion_task_id?: string | null;
};
