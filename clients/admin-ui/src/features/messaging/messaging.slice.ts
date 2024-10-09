import { baseApi } from "~/features/common/api.slice";

import {
  ConfigMessagingDetailsRequest,
  ConfigMessagingRequest,
  ConfigMessagingSecretsRequest,
} from "./types";

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
    createMessagingConfiguration: build.mutation<
      any,
      ConfigMessagingDetailsRequest
    >({
      query: (params) => ({
        url: `messaging/default`,
        method: "PUT",
        body: params,
      }),
    }),
    getActiveMessagingProvider: build.query<any, void>({
      query: () => ({
        url: `messaging/default/active`,
      }),
    }),
    createMessagingConfigurationSecrets: build.mutation<
      any,
      ConfigMessagingSecretsRequest
    >({
      query: (params) => ({
        url: `messaging/default/${params.service_type}/secret`,
        method: "PUT",
        body: params.details,
      }),
    }),
    getMessagingConfigurationDetails: build.query<any, ConfigMessagingRequest>({
      query: (params) => ({
        url: `messaging/default/${params.type}`,
      }),
    }),
  }),
});

export const {
  useGetEmailInviteStatusQuery,
  useGetActiveMessagingProviderQuery,
  useCreateMessagingConfigurationMutation,
  useCreateMessagingConfigurationSecretsMutation,
  useGetMessagingConfigurationDetailsQuery,
} = messagingApi;
