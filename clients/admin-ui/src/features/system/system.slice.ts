import { createSelector } from "@reduxjs/toolkit";

import { baseApi } from "~/features/common/api.slice";
import { buildArrayQueryParams } from "~/features/common/utils";
import { SystemColumnKeys } from "~/features/system/useSystemsTable";
import {
  BulkPutConnectionConfiguration,
  ConnectionConfigurationResponse,
  CreateConnectionConfigurationWithSecrets,
  Page_BasicSystemResponseExtended_,
  System,
  SystemResponse,
  SystemSchemaExtended,
  TestStatusMessage,
} from "~/types/api";
import {
  PaginationQueryParams,
  SearchQueryParams,
  SortQueryParams,
} from "~/types/query-params";

interface SystemDeleteResponse {
  message: string;
  resource: System;
}

interface UpsertResponse {
  message: string;
  inserted: number;
  updated: number;
}

interface BulkAssignStewardRequest {
  data_steward: string;
  system_keys: string[];
}

export type ConnectionConfigSecretsRequest = {
  systemFidesKey: string;
  secrets: {
    [key: string]: any;
  };
};

export type GetSystemsQueryParams = {
  data_stewards?: string[];
  system_groups?: string[];
};

const systemApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getSystems: build.query<
      Page_BasicSystemResponseExtended_,
      PaginationQueryParams &
        SearchQueryParams &
        GetSystemsQueryParams &
        SortQueryParams<SystemColumnKeys>
    >({
      query: ({
        data_stewards,
        system_groups,
        sort_by = [SystemColumnKeys.NAME],
        ...params
      }) => {
        const sortByArray = Array.isArray(sort_by) ? sort_by : [sort_by];
        const urlParams = buildArrayQueryParams({
          data_stewards,
          system_groups,
          sort_by: sortByArray,
        });

        return {
          method: "GET",
          url: `system?${urlParams.toString()}`,
          params,
        };
      },
      providesTags: () => ["System"],
    }),
    getAllSystems: build.query<SystemResponse[], void>({
      query: () => ({ url: `system` }),
      providesTags: () => ["System"],
    }),
    getSystemByFidesKey: build.query<SystemResponse, string>({
      query: (fides_key) => ({ url: `system/${fides_key}` }),
      providesTags: ["System"],
    }),
    // we accept 'unknown' as well since the user can paste anything in, and we rely
    // on the backend to do the validation for us
    createSystem: build.mutation<SystemResponse, System | unknown>({
      query: (body) => ({
        url: `system`,
        method: "POST",
        body,
      }),
      invalidatesTags: () => [
        "Datamap",
        "System",
        "Datastore Connection",
        "System Vendors",
        "Privacy Notices",
      ],
    }),
    deleteSystem: build.mutation<SystemDeleteResponse, string>({
      query: (key) => ({
        url: `system/${key}`,
        params: { resource_type: "system" },
        method: "DELETE",
      }),
      invalidatesTags: [
        "Datamap",
        "System",
        "Datastore Connection",
        "Privacy Notices",
        "System Vendors",
      ],
    }),
    bulkDeleteSystems: build.mutation<SystemDeleteResponse, string[]>({
      query: (keys) => ({
        url: `system/bulk-delete`,
        method: "POST",
        body: keys,
      }),
      invalidatesTags: [
        "Datamap",
        "System",
        "Datastore Connection",
        "Privacy Notices",
        "System Vendors",
      ],
    }),
    upsertSystems: build.mutation<UpsertResponse, System[]>({
      query: (systems) => ({
        url: `system/upsert`,
        method: "POST",
        body: systems,
      }),
      invalidatesTags: [
        "Datamap",
        "System",
        "Datastore Connection",
        "System History",
        "System Vendors",
      ],
    }),
    updateSystem: build.mutation<
      SystemResponse,
      Partial<SystemSchemaExtended> & Pick<SystemSchemaExtended, "fides_key">
    >({
      query: ({ ...patch }) => ({
        url: `system`,
        params: { resource_type: "system" },
        method: "PUT",
        body: patch,
      }),
      invalidatesTags: [
        "Datamap",
        "System",
        "Privacy Notices",
        "Datastore Connection",
        "System History",
        "System Vendors",
      ],
    }),
    patchSystemConnectionConfigs: build.mutation<
      BulkPutConnectionConfiguration,
      {
        systemFidesKey: string;
        connectionConfigs: Omit<
          CreateConnectionConfigurationWithSecrets,
          "created_at"
        >[];
      }
    >({
      query: ({ systemFidesKey, connectionConfigs }) => ({
        url: `/system/${systemFidesKey}/connection`,
        method: "PATCH",
        body: connectionConfigs,
      }),
      invalidatesTags: ["Datamap", "System", "Datastore Connection"],
    }),
    patchSystemConnectionSecrets: build.mutation<
      TestStatusMessage,
      ConnectionConfigSecretsRequest
    >({
      query: ({ secrets, systemFidesKey }) => ({
        url: `/system/${systemFidesKey}/connection/secrets?verify=false`,
        method: "PATCH",
        body: secrets,
      }),
      invalidatesTags: () => ["System", "Datastore Connection"],
    }),
    getSystemConnectionConfigs: build.query<
      ConnectionConfigurationResponse[],
      string
    >({
      query: (systemFidesKey) => ({
        url: `/system/${systemFidesKey}/connection`,
      }),
      providesTags: ["Datamap", "System", "Datastore Connection"],
    }),
    deleteSystemConnectionConfig: build.mutation({
      query: (systemFidesKey) => ({
        url: `/system/${systemFidesKey}/connection`,
        method: "DELETE",
      }),
      invalidatesTags: () => ["Datastore Connection", "System"],
    }),
    bulkAssignSteward: build.mutation<void, BulkAssignStewardRequest>({
      query: ({ data_steward, system_keys }) => ({
        url: `/system/assign-steward`,
        method: "POST",
        body: { data_steward, system_keys },
      }),
      invalidatesTags: () => ["System"],
    }),
  }),
});

export const {
  useGetSystemsQuery,
  useLazyGetSystemsQuery,
  useGetAllSystemsQuery,
  useGetSystemByFidesKeyQuery,
  useCreateSystemMutation,
  useUpdateSystemMutation,
  useDeleteSystemMutation,
  useBulkDeleteSystemsMutation,
  useUpsertSystemsMutation,
  usePatchSystemConnectionConfigsMutation,
  useDeleteSystemConnectionConfigMutation,
  useGetSystemConnectionConfigsQuery,
  usePatchSystemConnectionSecretsMutation,
  useLazyGetSystemByFidesKeyQuery,
  useBulkAssignStewardMutation,
} = systemApi;

export interface State {
  activeSystem?: System;
  activeClassifySystemFidesKey?: string;
  systemsToClassify?: System[];
}

/**
 * Selects the number of systems
 * By using the paginated getSystems endpoint, we can get the total number of systems
 */
export const selectSystemsCount = createSelector(
  [
    (RootState) => RootState,
    systemApi.endpoints.getSystems.select({ page: 1, size: 1 }),
  ],
  (RootState, { data }) => data?.total || 0,
);
