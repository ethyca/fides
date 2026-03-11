export interface JiraTicketResult {
  ticket_id: string;
  ticket_key: string;
  ticket_url: string;
  status: string;
  status_category: string | null;
  created_at: string | null;
  updated_at: string | null;
}
