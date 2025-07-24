import { baseApi } from "~/features/common/api.slice";
import { ManualTaskResponse } from "~/types/api";

import { PLUS_CONNECTION_API_ROUTE } from "../../constants";

export const connectionManualTasksApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getManualTaskConfig: build.query<
      ManualTaskResponse,
      { connectionKey: string }
    >({
      query: ({ connectionKey }) => ({
        url: `${PLUS_CONNECTION_API_ROUTE}/${connectionKey}/manual-task`,
        method: "GET",
      }),
      providesTags: () => ["Manual Tasks"],
    }),
    assignUsersToManualTask: build.mutation<
      ManualTaskResponse,
      { connectionKey: string; userIds: string[] }
    >({
      query: ({ connectionKey, userIds }) => ({
        url: `${PLUS_CONNECTION_API_ROUTE}/${connectionKey}/manual-task/assign-users`,
        method: "PUT",
        body: userIds,
      }),
      invalidatesTags: () => ["Manual Tasks"],
    }),
  }),
});

export const {
  useGetManualTaskConfigQuery,
  useAssignUsersToManualTaskMutation,
} = connectionManualTasksApi;
