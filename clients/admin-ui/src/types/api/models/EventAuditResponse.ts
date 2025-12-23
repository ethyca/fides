/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response model for event audit log entries.
 */
export type EventAuditResponse = {
  id: string;
  created_at: string;
  event_type: string;
  status: string;
  resource_type?: string | null;
  resource_identifier?: string | null;
  description?: string | null;
  event_details?: null;
  user_id?: string | null;
};
