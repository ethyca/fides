/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response schema for a single system history entry
 */
export type SystemHistoryResponse = {
  edited_by?: string | null;
  system_id: string;
  before: any;
  after: any;
  created_at: string;
};
