import { StatusType } from "~/types/api";

export interface JiraTicketResult {
  ticket_id: string;
  /** ManualTaskInstance ID — used as the `instance_id` path param for retry/refresh. */
  instance_id: string | null;
  instance_status: StatusType | null;
  ticket_key: string;
  ticket_url: string | null;
  status: string;
  status_category: string | null;
  created_at: string | null;
  updated_at: string | null;
}
