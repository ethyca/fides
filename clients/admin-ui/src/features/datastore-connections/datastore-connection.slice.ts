import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

import { baseApi } from "~/features/common/api.slice";
import {
  BulkPutDataset,
  ConnectionConfigurationResponse,
  CreateConnectionConfigurationWithSecrets,
  Page_DatasetConfigSchema_,
  SystemType,
} from "~/types/api";

import type { RootState } from "../../app/store";
import { CONNECTION_ROUTE } from "../../constants";
import { DisabledStatus, TestingStatus } from "./constants";
import {
  CreateAccessManualWebhookRequest,
  CreateAccessManualWebhookResponse,
  CreateSaasConnectionConfigRequest,
  CreateSaasConnectionConfigResponse,
  DatastoreConnectionParams,
  DatastoreConnectionResponse,
  DatastoreConnectionSecretsRequest,
  DatastoreConnectionSecretsResponse,
  DatastoreConnectionsResponse,
  DatastoreConnectionStatus,
  GetAccessManualWebhookResponse,
  GetAllEnabledAccessManualWebhooksResponse,
  PatchAccessManualWebhookRequest,
  PatchAccessManualWebhookResponse,
  PatchDatasetsConfigRequest,
} from "./types";

function mapFiltersToSearchParams({
  search,
  page,
  size,
  connection_type,
  test_status,
  system_type,
  disabled_status,
  orphaned_from_system,
}: Partial<DatastoreConnectionParams>): string {
  let queryString = "";
  if (connection_type) {
    connection_type.forEach((d) => {
      queryString += queryString
        ? `&connection_type=${d}`
        : `connection_type=${d}`;
    });
  }

  if (search) {
    queryString += queryString ? `&search=${search}` : `search=${search}`;
  }
  if (typeof size !== "undefined") {
    queryString += queryString ? `&size=${size}` : `size=${size}`;
  }
  if (page) {
    queryString += queryString ? `&page=${page}` : `page=${page}`;
  }
  if (test_status) {
    queryString += queryString
      ? `&test_status=${test_status}`
      : `test_status=${test_status}`;
  }
  if (system_type) {
    queryString += queryString
      ? `&system_type=${system_type}`
      : `system_type=${system_type}`;
  }
  if (disabled_status) {
    const value = disabled_status === DisabledStatus.DISABLED;
    queryString += queryString ? `&disabled=${value}` : `disabled=${value}`;
  }

  if (typeof orphaned_from_system !== "undefined") {
    queryString += queryString
      ? `&orphaned_from_system=${orphaned_from_system}`
      : `orphaned_from_system=${orphaned_from_system}`;
  }

  return queryString ? `?${queryString}` : "";
}
const initialState: DatastoreConnectionParams = {
  search: "",
  page: 1,
  size: 25,
  orphaned_from_system: true,
};

export type CreateSaasConnectionConfig = {
  connectionConfig: Omit<CreateSaasConnectionConfigRequest, "name">;
  systemFidesKey: string;
};

export const datastoreConnectionSlice = createSlice({
  name: "datastoreConnections",
  initialState,
  reducers: {
    setSearch: (state, action: PayloadAction<string>) => ({
      ...state,
      page: initialState.page,
      search: action.payload,
    }),
    setConnectionType: (state, action: PayloadAction<string[]>) => ({
      ...state,
      page: initialState.page,
      connection_type: action.payload,
    }),
    setTestingStatus: (
      state,
      action: PayloadAction<TestingStatus | string>,
    ) => ({
      ...state,
      page: initialState.page,
      test_status: action.payload as TestingStatus,
    }),
    setSystemType: (state, action: PayloadAction<SystemType | string>) => ({
      ...state,
      page: initialState.page,
      system_type: action.payload as SystemType,
    }),
    setDisabledStatus: (
      state,
      action: PayloadAction<DisabledStatus | string>,
    ) => ({
      ...state,
      page: initialState.page,
      disabled_status: action.payload as DisabledStatus,
    }),
    setPage: (state, action: PayloadAction<number>) => ({
      ...state,
      page: action.payload,
    }),
    setSize: (state, action: PayloadAction<number>) => ({
      ...state,
      page: initialState.page,
      size: action.payload,
    }),
    setOrphanedFromSystem: (state, action: PayloadAction<boolean>) => ({
      ...state,
      page: initialState.page,
      orphaned_from_system: action.payload,
    }),
  },
});

export const {
  setSearch,
  setSize,
  setPage,
  setConnectionType,
  setSystemType,
  setTestingStatus,
  setDisabledStatus,
  setOrphanedFromSystem,
} = datastoreConnectionSlice.actions;

export const selectDatastoreConnectionFilters = (state: RootState) =>
  state.datastoreConnections;

export const { reducer } = datastoreConnectionSlice;

export const datastoreConnectionApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAuthorizationUrl: build.query<string, string>({
      query: (connectionKey) => ({
        url: `${CONNECTION_ROUTE}/${connectionKey}/authorize`,
        method: "GET",
      }),
      providesTags: () => ["Datastore Connection"],
    }),
    createAccessManualWebhook: build.mutation<
      CreateAccessManualWebhookResponse,
      CreateAccessManualWebhookRequest
    >({
      query: (params) => ({
        url: `${CONNECTION_ROUTE}/${params.connection_key}/access_manual_webhook`,
        method: "POST",
        body: params.body,
      }),
      invalidatesTags: () => ["Datastore Connection"],
    }),
    createSassConnectionConfig: build.mutation<
      CreateSaasConnectionConfigResponse,
      CreateSaasConnectionConfig
    >({
      query: (params) => {
        const url = `/system/${params.systemFidesKey}${CONNECTION_ROUTE}/instantiate/${params.connectionConfig.saas_connector_type}`;

        return {
          url,
          method: "POST",
          body: { ...params.connectionConfig },
        };
      },
      // Creating a connection config also creates a dataset behind the scenes
      invalidatesTags: () => ["Datastore Connection", "Datasets", "System"],
    }),

    createUnlinkedSassConnectionConfig: build.mutation<
      CreateSaasConnectionConfigResponse,
      CreateSaasConnectionConfigRequest
    >({
      query: (params) => {
        const url = `${CONNECTION_ROUTE}/instantiate/${params.saas_connector_type}`;

        return {
          url,
          method: "POST",
          body: { ...params },
        };
      },
      // Creating a connection config also creates a dataset behind the scenes
      invalidatesTags: () => ["Datastore Connection", "Datasets", "System"],
    }),
    deleteDatastoreConnection: build.mutation({
      query: (id) => ({
        url: `${CONNECTION_ROUTE}/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: () => ["Datastore Connection", "System"],
    }),
    getAccessManualHook: build.query<GetAccessManualWebhookResponse, string>({
      query: (key) => ({
        url: `${CONNECTION_ROUTE}/${key}/access_manual_webhook`,
      }),
      providesTags: () => ["Datastore Connection"],
    }),
    getAllDatastoreConnections: build.query<
      DatastoreConnectionsResponse,
      Partial<DatastoreConnectionParams>
    >({
      query: (filters) => ({
        url: CONNECTION_ROUTE + mapFiltersToSearchParams(filters),
      }),
      providesTags: () => ["Datastore Connection"],
    }),
    getAllEnabledAccessManualHooks: build.query<
      GetAllEnabledAccessManualWebhooksResponse,
      void
    >({
      query: () => ({
        url: `access_manual_webhook`,
      }),
      providesTags: () => ["Datastore Connection"],
    }),
    getDatastoreConnectionByKey: build.query<
      ConnectionConfigurationResponse,
      string
    >({
      query: (key) => ({
        url: `${CONNECTION_ROUTE}/${key}`,
      }),
      providesTags: (result) => [
        { type: "Datastore Connection", id: result?.key },
      ],
      keepUnusedDataFor: 1,
    }),
    getConnectionConfigDatasetConfigs: build.query<
      Page_DatasetConfigSchema_,
      string
    >({
      query: (key) => ({
        url: `${CONNECTION_ROUTE}/${key}/datasetconfig`,
      }),
      providesTags: () => ["Datastore Connection"],
    }),
    getDatastoreConnectionStatus: build.query<
      DatastoreConnectionStatus,
      string
    >({
      query: (id) => ({
        url: `${CONNECTION_ROUTE}/${id}/test`,
      }),
      providesTags: () => ["Datastore Connection"],
      async onQueryStarted(key, { dispatch, queryFulfilled, getState }) {
        await queryFulfilled;

        const request = dispatch(
          datastoreConnectionApi.endpoints.getDatastoreConnectionByKey.initiate(
            key,
          ),
        );
        const result = await request.unwrap();
        request.unsubscribe();

        const state = getState() as RootState;
        const filters = selectDatastoreConnectionFilters(state);

        dispatch(
          datastoreConnectionApi.util.updateQueryData(
            "getAllDatastoreConnections",
            filters,
            (draft) => {
              const newList = draft.items.map((d) => {
                if (d.key === key) {
                  return { ...result };
                }
                return { ...d };
              });
              // eslint-disable-next-line no-param-reassign
              draft.items = newList;
            },
          ),
        );
      },
    }),
    patchAccessManualWebhook: build.mutation<
      PatchAccessManualWebhookResponse,
      PatchAccessManualWebhookRequest
    >({
      query: (params) => ({
        url: `${CONNECTION_ROUTE}/${params.connection_key}/access_manual_webhook`,
        method: "PATCH",
        body: params.body,
      }),
      invalidatesTags: () => ["Datastore Connection"],
    }),
    patchDatasetConfigs: build.mutation<
      BulkPutDataset,
      PatchDatasetsConfigRequest
    >({
      query: (params) => ({
        url: `${CONNECTION_ROUTE}/${params.connection_key}/datasetconfig`,
        method: "PATCH",
        body: params.dataset_pairs,
      }),
      invalidatesTags: () => ["Datastore Connection", "Datasets"],
    }),
    putDatasetConfigs: build.mutation<
      BulkPutDataset,
      PatchDatasetsConfigRequest
    >({
      query: (params) => ({
        url: `${CONNECTION_ROUTE}/${params.connection_key}/datasetconfig`,
        method: "PUT",
        body: params.dataset_pairs,
      }),
      invalidatesTags: () => ["Datastore Connection", "Datasets"],
    }),
    patchDatastoreConnection: build.mutation<
      DatastoreConnectionResponse,
      CreateConnectionConfigurationWithSecrets
    >({
      query: (params) => ({
        url: `${CONNECTION_ROUTE}`,
        method: "PATCH",
        body: [params],
      }),
      invalidatesTags: () => ["Datastore Connection", "Datasets"],
    }),
    patchDatastoreConnections: build.mutation({
      query: ({ key, name, disabled, connection_type, access }) => ({
        url: CONNECTION_ROUTE,
        method: "PATCH",
        body: [{ key, name, disabled, connection_type, access }],
      }),
      invalidatesTags: () => ["Datastore Connection", "Datasets", "System"],
    }),
    updateDatastoreConnectionSecrets: build.mutation<
      DatastoreConnectionSecretsResponse,
      DatastoreConnectionSecretsRequest
    >({
      query: (params) => ({
        url: `${CONNECTION_ROUTE}/${params.connection_key}/secret?verify=false`,
        method: "PUT",
        body: params.secrets,
      }),
      invalidatesTags: () => ["Datastore Connection"],
    }),
    patchDatastoreConnectionSecrets: build.mutation<
      DatastoreConnectionSecretsResponse,
      DatastoreConnectionSecretsRequest
    >({
      query: (params) => ({
        url: `${CONNECTION_ROUTE}/${params.connection_key}/secret?verify=false`,
        method: "PATCH",
        body: params.secrets,
      }),
      invalidatesTags: () => ["Datastore Connection"],
    }),
    testDatastoreConnectionDatasets: build.mutation<
      { privacy_request_id: string },
      {
        connection_key: string;
        dataset_key: string;
        identities: Record<string, any>;
        policy_key: string;
      }
    >({
      query: (params) => ({
        url: `${CONNECTION_ROUTE}/${params.connection_key}/dataset/${params.dataset_key}/test`,
        method: "POST",
        body: { identities: params.identities, policy_key: params.policy_key },
      }),
    }),
    getDatasetInputs: build.query<
      any,
      { connectionKey: string; datasetKey: string }
    >({
      query: ({ connectionKey, datasetKey }) => ({
        url: `${CONNECTION_ROUTE}/${connectionKey}/dataset/${datasetKey}/inputs`,
        method: "GET",
      }),
      providesTags: () => ["Datastore Connection"],
    }),
    getDatasetReachability: build.query<
      { reachable: boolean; details: string },
      { connectionKey: string; datasetKey: string }
    >({
      query: ({ connectionKey, datasetKey }) => ({
        url: `${CONNECTION_ROUTE}/${connectionKey}/dataset/${datasetKey}/reachability`,
        method: "GET",
      }),
      providesTags: () => ["Datastore Connection"],
    }),
  }),
});

export const {
  useLazyGetAuthorizationUrlQuery,
  useCreateAccessManualWebhookMutation,
  useCreateSassConnectionConfigMutation,
  useCreateUnlinkedSassConnectionConfigMutation,
  useGetAccessManualHookQuery,
  useGetAllEnabledAccessManualHooksQuery,
  useGetAllDatastoreConnectionsQuery,
  useGetConnectionConfigDatasetConfigsQuery,
  useGetDatastoreConnectionByKeyQuery,
  useDeleteDatastoreConnectionMutation,
  useLazyGetDatastoreConnectionStatusQuery,
  usePatchAccessManualWebhookMutation,
  usePatchDatasetConfigsMutation,
  usePutDatasetConfigsMutation,
  usePatchDatastoreConnectionMutation,
  usePatchDatastoreConnectionsMutation,
  useUpdateDatastoreConnectionSecretsMutation,
  usePatchDatastoreConnectionSecretsMutation,
  useTestDatastoreConnectionDatasetsMutation,
  useGetDatasetInputsQuery,
  useGetDatasetReachabilityQuery,
} = datastoreConnectionApi;

/**
 * This constant is used for a `getAllDatastoreConnections` query that is run as a global
 * subscription just to check whether the user has any connections at all.
 */
export const INITIAL_CONNECTIONS_FILTERS: DatastoreConnectionParams = {
  search: "",
  page: 1,
  size: 5,
};

/**
 * Returns the globally cached datastore connections response.
 */
export const selectInitialConnections = createSelector(
  [
    (RootState) => RootState,
    datastoreConnectionApi.endpoints.getAllDatastoreConnections.select(
      INITIAL_CONNECTIONS_FILTERS,
    ),
  ],
  (RootState, { data }) => data,
);
