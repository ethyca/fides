/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Data required to create a Jira ticket.
 *
 * Used by :meth:`~fidesplus.jira.jira_client.JiraClient.create_issue` and
 * :meth:`~fidesplus.jira.jira_ticket_service.JiraTicketService.create_ticket_for_privacy_request`.
 */
export type JiraTicketData = {
  /**
   * Jira project key (e.g., 'PRIV')
   */
  project_key: string;
  /**
   * Jira issue type name (e.g., 'Task')
   */
  issue_type: string;
  /**
   * Rendered ticket title
   */
  summary: string;
  /**
   * Rendered ticket description
   */
  description: string;
  /**
   * Ticket due date
   */
  due_date?: string | null;
};
