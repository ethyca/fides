import { baseApi } from "~/features/common/api.slice";

import { JiraTicketResult } from "./types";

interface LinkJiraTicketRequest {
  privacy_request_id: string;
  ticket_key: string;
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
  }),
});

export const { useGetJiraTicketsQuery, useLinkJiraTicketMutation } =
  privacyRequestJiraTicketsApi;
