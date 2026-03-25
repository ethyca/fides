/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Lightweight Jira ticket info embedded in privacy request responses.
 */
export type JiraTicketSummary = {
  /**
   * Jira issue key (e.g., 'PRIV-123')
   */
  ticket_key: string;
  /**
   * Full URL to the Jira issue
   */
  ticket_url: string;
  /**
   * Current Jira status (e.g., 'To Do', 'In Progress', 'Done')
   */
  status?: string | null;
};
