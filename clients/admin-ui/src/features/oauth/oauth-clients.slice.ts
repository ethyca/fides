import { baseApi } from "~/features/common/api.slice";
import {
  ClientCreatedResponse,
  ClientResponse,
  ClientSecretRotateResponse,
  Page_ClientResponse_,
} from "~/types/api";

export interface ClientCreateParams {
  name?: string;
  description?: string;
  scopes?: string[];
}

export interface ClientUpdateParams {
  client_id: string;
  name?: string;
  description?: string;
  scopes?: string[];
}

const oauthClientsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    listOAuthClients: build.query<
      Page_ClientResponse_,
      { page?: number; size?: number }
    >({
      query: ({ page = 1, size = 25 } = {}) => ({
        url: `oauth/client`,
        params: { page, size },
      }),
      providesTags: ["OAuth Client"],
    }),
    getOAuthClient: build.query<ClientResponse, string>({
      query: (clientId) => ({ url: `oauth/client/${clientId}` }),
      providesTags: (_result, _error, clientId) => [
        { type: "OAuth Client", id: clientId },
      ],
    }),
    createOAuthClient: build.mutation<
      ClientCreatedResponse,
      ClientCreateParams
    >({
      query: (body) => ({
        url: `oauth/client`,
        method: "POST",
        body,
      }),
      invalidatesTags: ["OAuth Client"],
    }),
    updateOAuthClient: build.mutation<ClientResponse, ClientUpdateParams>({
      query: ({ client_id, ...body }) => ({
        url: `oauth/client/${client_id}`,
        method: "PUT",
        body,
      }),
      invalidatesTags: (_result, _error, { client_id }) => [
        "OAuth Client",
        { type: "OAuth Client", id: client_id },
      ],
    }),
    deleteOAuthClient: build.mutation<void, string>({
      query: (clientId) => ({
        url: `oauth/client/${clientId}`,
        method: "DELETE",
      }),
      invalidatesTags: ["OAuth Client"],
    }),
    rotateOAuthClientSecret: build.mutation<ClientSecretRotateResponse, string>(
      {
        query: (clientId) => ({
          url: `oauth/client/${clientId}/secret`,
          method: "POST",
        }),
      },
    ),
  }),
});

export const {
  useListOAuthClientsQuery,
  useGetOAuthClientQuery,
  useCreateOAuthClientMutation,
  useUpdateOAuthClientMutation,
  useDeleteOAuthClientMutation,
  useRotateOAuthClientSecretMutation,
} = oauthClientsApi;
