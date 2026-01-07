import { baseApi } from "~/features/common/api.slice";
import { ConditionGroup, ManualTaskResponse } from "~/types/api";

import { PLUS_CONNECTION_API_ROUTE } from "../../constants";
import { PrivacyRequestFieldsResponse } from "../integrations/configure-tasks/types";

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

    updateDependencyConditions: build.mutation<
      void,
      { connectionKey: string; conditions: ConditionGroup[] }
    >({
      query: ({ connectionKey, conditions }) => ({
        url: `${PLUS_CONNECTION_API_ROUTE}/${connectionKey}/manual-task/dependency-conditions`,
        method: "PUT",
        body: conditions,
      }),
      invalidatesTags: () => ["Manual Tasks"],
    }),

    getPrivacyRequestFields: build.query<
      PrivacyRequestFieldsResponse,
      { connectionKey: string }
    >({
      query: ({ connectionKey }) => ({
        url: `${PLUS_CONNECTION_API_ROUTE}/${connectionKey}/manual-task/dependency-conditions/privacy-request-fields`,
        method: "GET",
      }),
      providesTags: () => ["Allowed Conditions Fields"],
    }),
  }),
});

export const {
  useGetManualTaskConfigQuery,
  useAssignUsersToManualTaskMutation,
  useUpdateDependencyConditionsMutation,
  useGetPrivacyRequestFieldsQuery,
} = connectionManualTasksApi;
