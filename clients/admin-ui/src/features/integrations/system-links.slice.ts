import { PLUS_CONNECTION_API_ROUTE } from "~/constants";
import { baseApi } from "~/features/common/api.slice";
import {
  SystemConnectionLinkType,
  SystemLink,
} from "~/mocks/system-links/data";

export interface SetSystemLinksRequest {
  links: Array<{
    system_fides_key: string;
    link_type: SystemConnectionLinkType;
  }>;
}

export interface SystemLinksResponse {
  links: SystemLink[];
}

export const systemLinksApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getSystemLinks: build.query<SystemLink[], string>({
      query: (connectionKey) => ({
        url: `${PLUS_CONNECTION_API_ROUTE}/${connectionKey}/system-links`,
        method: "GET",
      }),
      providesTags: (result, _error, connectionKey) => [
        { type: "System Links", id: connectionKey },
      ],
    }),
    setSystemLinks: build.mutation<
      SystemLinksResponse,
      { connectionKey: string; body: SetSystemLinksRequest }
    >({
      query: ({ connectionKey, body }) => ({
        url: `${PLUS_CONNECTION_API_ROUTE}/${connectionKey}/system-links`,
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
        linkType?: SystemConnectionLinkType;
      }
    >({
      query: ({ connectionKey, systemFidesKey, linkType }) => {
        const url = `${PLUS_CONNECTION_API_ROUTE}/${connectionKey}/system-links/${systemFidesKey}`;
        const params = linkType ? `?link_type=${linkType}` : "";
        return {
          url: url + params,
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
