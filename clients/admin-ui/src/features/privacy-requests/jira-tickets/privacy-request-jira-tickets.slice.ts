import { baseApi } from "~/features/common/api.slice";

import { JiraTicketResult } from "./types";

interface LinkJiraTicketRequest {
  privacy_request_id: string;
  ticket_key: string;
}

interface TicketInstanceRequest {
  privacy_request_id: string;
  instance_id: string;
}

const privacyRequestJiraTicketsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getJiraTickets: build.query<
      JiraTicketResult[],
      { privacy_request_id: string }
    >({
      query: ({ privacy_request_id }) => ({
        url: `plus/privacy-request/${privacy_request_id}/jira-tickets`,
        method: "GET",
      }),
      providesTags: ["Jira Tickets"],
    }),
    linkJiraTicket: build.mutation<JiraTicketResult, LinkJiraTicketRequest>({
      query: ({ privacy_request_id, ticket_key }) => ({
        url: `plus/privacy-request/${privacy_request_id}/jira-tickets/link`,
        method: "POST",
        body: { ticket_key },
      }),
      invalidatesTags: ["Jira Tickets"],
    }),
    retryJiraTicket: build.mutation<JiraTicketResult, TicketInstanceRequest>({
      query: ({ privacy_request_id, instance_id }) => ({
        url: `plus/privacy-request/${privacy_request_id}/jira-tickets/${instance_id}/retry`,
        method: "POST",
      }),
      invalidatesTags: ["Jira Tickets"],
    }),
    refreshJiraTicket: build.mutation<JiraTicketResult, TicketInstanceRequest>({
      query: ({ privacy_request_id, instance_id }) => ({
        url: `plus/privacy-request/${privacy_request_id}/jira-tickets/${instance_id}/refresh`,
        method: "POST",
      }),
      invalidatesTags: ["Jira Tickets"],
    }),
  }),
});

export const {
  useGetJiraTicketsQuery,
  useLinkJiraTicketMutation,
  useRetryJiraTicketMutation,
  useRefreshJiraTicketMutation,
} = privacyRequestJiraTicketsApi;
