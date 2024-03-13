import { baseApi } from "~/features/common/api.slice";

export type UserEmailInviteStatus = {
  enabled: boolean;
};

// Messaging API
const messagingApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getEmailInviteStatus: build.query<UserEmailInviteStatus, void>({
      query: () => ({ url: `/messaging/email-invite/status` }),
      providesTags: () => ["Email Invite Status"],
    }),
  }),
});

export const { useGetEmailInviteStatusQuery } = messagingApi;
