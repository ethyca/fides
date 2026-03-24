export interface JiraTicketResult {
  ticket_id: string;
  /** ManualTaskInstance ID — used as the `instance_id` path param for retry/refresh.
   * Pending backend fix to include this field in the response. */
  instance_id?: string;
  ticket_key: string;
  ticket_url: string;
  status: string;
  status_category: string | null;
  created_at: string | null;
  updated_at: string | null;
}
