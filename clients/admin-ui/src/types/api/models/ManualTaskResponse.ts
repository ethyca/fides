/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AssignedUserSummary } from './AssignedUserSummary';
import type { ManualTaskParentEntityType } from './ManualTaskParentEntityType';
import type { StatusType } from './StatusType';

/**
 * Schema for manual task response.
 */
export type ManualTaskResponse = {
  /**
   * Task ID
   */
  id: string;
  /**
   * Parent entity ID
   */
  parent_entity_id: string;
  /**
   * Parent entity type
   */
  parent_entity_type: ManualTaskParentEntityType;
  /**
   * Task status
   */
  status: StatusType;
  /**
   * Creation timestamp
   */
  created_at: string;
  /**
   * Last update timestamp
   */
  updated_at: string;
  /**
   * Users assigned to the manual task
   */
  assigned_users?: (Array<AssignedUserSummary> | null);
  /**
   * Dependency conditions
   */
  dependency_conditions?: null;
  /**
   * Validation warnings for dependency conditions
   */
  validation_warnings?: null;
};

