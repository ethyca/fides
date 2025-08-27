import { baseApi } from "~/features/common/api.slice";
import { ConfigMessagingSecretsRequest } from "~/features/privacy-requests/types";
import { Page_MessagingConfigResponse_ } from "~/types/api";

import { ConfigMessagingDetailsRequest, ConfigMessagingRequest } from "./types";

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
        url: `messaging/config`,
        method: "POST",
        body: params,
      }),
      invalidatesTags: ["Messaging Config"],
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
      invalidatesTags: ["Messaging Config"],
    }),
    getMessagingConfigurationDetails: build.query<any, ConfigMessagingRequest>({
      query: (params) => ({
        url: `messaging/default/${params.type}`,
      }),
    }),
    getMessagingConfigurations: build.query<
      Page_MessagingConfigResponse_,
      void
    >({
      query: () => ({
        url: `messaging/config`,
      }),
      providesTags: ["Messaging Config"],
    }),
    getMessagingConfigurationByKey: build.query<any, { key: string }>({
      query: (params) => ({
        url: `messaging/config/${params.key}`,
      }),
      providesTags: ["Messaging Config"],
    }),
    createTestConnectionMessage: build.mutation<any, any>({
      query: (params) => ({
        url: `messaging/test/${params.service_type}`,
        method: "POST",
        body: params.details,
      }),
      invalidatesTags: ["Messaging Config"],
    }),
    updateMessagingConfigurationByKey: build.mutation<
      any,
      { key: string; config: any }
    >({
      query: (params) => ({
        url: `messaging/config/${params.key}`,
        method: "PATCH",
        body: params.config,
      }),
      invalidatesTags: ["Messaging Config"],
    }),

    updateMessagingConfigurationSecretsByKey: build.mutation<
      any,
      { key: string; secrets: any }
    >({
      query: (params) => ({
        url: `messaging/config/${params.key}/secret`,
        method: "PUT",
        body: params.secrets,
      }),
      invalidatesTags: ["Messaging Config"],
    }),
    deleteMessagingConfigurationByKey: build.mutation<any, { key: string }>({
      query: (params) => ({
        url: `messaging/config/${params.key}`,
        method: "DELETE",
      }),
      invalidatesTags: ["Messaging Config"],
    }),
  }),
});

export const {
  useGetEmailInviteStatusQuery,
  useGetActiveMessagingProviderQuery,
  useCreateMessagingConfigurationMutation,
  useCreateMessagingConfigurationSecretsMutation,
  useGetMessagingConfigurationDetailsQuery,
  useGetMessagingConfigurationsQuery,
  useGetMessagingConfigurationByKeyQuery,
  useUpdateMessagingConfigurationByKeyMutation,
  useUpdateMessagingConfigurationSecretsByKeyMutation,
  useCreateTestConnectionMessageMutation,
  useDeleteMessagingConfigurationByKeyMutation,
} = messagingApi;
