import { CONNECTION_ROUTE } from "~/constants";
import { baseApi } from "~/features/common/api.slice";

export interface SetSystemLinksRequest {
  links: Array<{
    system_fides_key: string;
  }>;
}

export interface SystemLinkResponse {
  system_fides_key: string;
  system_name: string | null;
  created_at: string;
}

export const systemLinksApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getSystemLinks: build.query<SystemLinkResponse[], string>({
      query: (connectionKey) => ({
        url: `${CONNECTION_ROUTE}/${connectionKey}/system-links`,
        method: "GET",
      }),
      providesTags: (result, _error, connectionKey) => [
        { type: "System Links", id: connectionKey },
      ],
    }),
    setSystemLinks: build.mutation<
      SystemLinkResponse,
      { connectionKey: string; body: SetSystemLinksRequest }
    >({
      query: ({ connectionKey, body }) => ({
        url: `${CONNECTION_ROUTE}/${connectionKey}/system-links`,
        method: "PUT",
        body,
      }),
      invalidatesTags: (result, _error, { connectionKey }) => [
        { type: "System Links", id: connectionKey },
        "Datastore Connection",
      ],
    }),
    deleteSystemLink: build.mutation<
      void,
      {
        connectionKey: string;
        systemFidesKey: string;
      }
    >({
      query: ({ connectionKey, systemFidesKey }) => {
        const url = `${CONNECTION_ROUTE}/${connectionKey}/system-links/${systemFidesKey}`;
        return {
          url,
          method: "DELETE",
        };
      },
      invalidatesTags: (result, _error, { connectionKey }) => [
        { type: "System Links", id: connectionKey },
        "Datastore Connection",
      ],
    }),
  }),
});

export const {
  useGetSystemLinksQuery,
  useSetSystemLinksMutation,
  useDeleteSystemLinkMutation,
} = systemLinksApi;
