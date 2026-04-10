import { baseApi } from "~/features/common/api.slice";

export interface IdentityGroupProviderResponse {
  id: string;
  key: string;
  name: string;
  provider_type: string;
  connection_config_key: string;
  domain: string;
  delegation_subject?: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface IdentityGroupProviderListResponse {
  items: IdentityGroupProviderResponse[];
  total: number;
  page: number;
  size: number;
}

export interface CreateIdentityGroupProviderRequest {
  key: string;
  name: string;
  provider_type: string;
  connection_config_key: string;
  enabled?: boolean;
}

export interface UpdateIdentityGroupProviderRequest {
  id: string;
  name?: string;
  enabled?: boolean;
}

export interface TestConnectionResponse {
  success: boolean;
  message: string;
}

const identityGroupProviderApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getIdentityGroupProviders: build.query<
      IdentityGroupProviderListResponse,
      { connection_config_key?: string }
    >({
      query: (params) => ({
        url: "identity-group-provider",
        method: "GET",
        params,
      }),
      providesTags: ["IdentityGroupProvider"],
    }),

    createIdentityGroupProvider: build.mutation<
      IdentityGroupProviderResponse,
      CreateIdentityGroupProviderRequest
    >({
      query: (body) => ({
        url: "identity-group-provider",
        method: "POST",
        body,
      }),
      invalidatesTags: ["IdentityGroupProvider", "DataConsumer"],
    }),

    updateIdentityGroupProvider: build.mutation<
      IdentityGroupProviderResponse,
      UpdateIdentityGroupProviderRequest
    >({
      query: ({ id, ...body }) => ({
        url: `identity-group-provider/${id}`,
        method: "PUT",
        body,
      }),
      invalidatesTags: ["IdentityGroupProvider"],
    }),

    deleteIdentityGroupProvider: build.mutation<void, string>({
      query: (id) => ({
        url: `identity-group-provider/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: ["IdentityGroupProvider", "DataConsumer"],
    }),

    testIdentityGroupProvider: build.mutation<TestConnectionResponse, string>({
      query: (id) => ({
        url: `identity-group-provider/${id}/test`,
        method: "POST",
      }),
    }),
  }),
});

export const {
  useGetIdentityGroupProvidersQuery,
  useCreateIdentityGroupProviderMutation,
  useUpdateIdentityGroupProviderMutation,
  useDeleteIdentityGroupProviderMutation,
  useTestIdentityGroupProviderMutation,
} = identityGroupProviderApi;
