import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import type { RootState } from "../../app/store";
import { BASE_URL, CONNECTION_ROUTE } from "../../constants";
import { selectToken } from "../auth";
import { addCommonHeaders } from "../common/CommonHeaders";
import {
  ConnectionType,
  DisabledStatus,
  SystemType,
  TestingStatus,
} from "./constants";
import {
  CreateAccessManualWebhookRequest,
  CreateAccessManualWebhookResponse,
  CreateSassConnectionConfigRequest,
  CreateSassConnectionConfigResponse,
  DatasetsReponse,
  DatastoreConnection,
  DatastoreConnectionParams,
  DatastoreConnectionRequest,
  DatastoreConnectionResponse,
  DatastoreConnectionSecretsRequest,
  DatastoreConnectionSecretsResponse,
  DatastoreConnectionsResponse,
  DatastoreConnectionStatus,
  GetAccessManualWebhookResponse,
  PatchAccessManualWebhookRequest,
  PatchAccessManualWebhookResponse,
  PatchDatasetsRequest,
} from "./types";

function mapFiltersToSearchParams({
  search,
  page,
  size,
  connection_type,
  test_status,
  system_type,
  disabled_status,
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

  return queryString ? `?${queryString}` : "";
}
const initialState: DatastoreConnectionParams = {
  search: "",
  page: 1,
  size: 25,
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
    setConnectionType: (state, action: PayloadAction<ConnectionType[]>) => ({
      ...state,
      page: initialState.page,
      connection_type: action.payload,
    }),
    setTestingStatus: (
      state,
      action: PayloadAction<TestingStatus | string>
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
      action: PayloadAction<DisabledStatus | string>
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
} = datastoreConnectionSlice.actions;
export const selectDatastoreConnectionFilters = (
  state: RootState
): DatastoreConnectionParams => ({
  search: state.datastoreConnections.search,
  page: state.datastoreConnections.page,
  size: state.datastoreConnections.size,
  connection_type: state.datastoreConnections.connection_type,
  system_type: state.datastoreConnections.system_type,
  test_status: state.datastoreConnections.test_status,
  disabled_status: state.datastoreConnections.disabled_status,
});

export const { reducer } = datastoreConnectionSlice;

export const datastoreConnectionApi = createApi({
  reducerPath: "datastoreConnectionApi",
  baseQuery: fetchBaseQuery({
    baseUrl: BASE_URL,
    prepareHeaders: (headers, { getState }) => {
      const token: string | null = selectToken(getState() as RootState);
      addCommonHeaders(headers, token);
      return headers;
    },
  }),
  tagTypes: ["DatastoreConnection"],
  endpoints: (build) => ({
    createAccessManualWebhook: build.mutation<
      CreateAccessManualWebhookResponse,
      CreateAccessManualWebhookRequest
    >({
      query: (params) => ({
        url: `${CONNECTION_ROUTE}/${params.connection_key}/access_manual_webhook`,
        method: "POST",
        body: params.body,
      }),
      invalidatesTags: () => ["DatastoreConnection"],
    }),
    createSassConnectionConfig: build.mutation<
      CreateSassConnectionConfigResponse,
      CreateSassConnectionConfigRequest
    >({
      query: (params) => ({
        url: `${CONNECTION_ROUTE}/instantiate/${params.saas_connector_type}`,
        method: "POST",
        body: { ...params },
      }),
      invalidatesTags: ["DatastoreConnection"],
    }),
    deleteDatastoreConnection: build.mutation({
      query: (id) => ({
        url: `${CONNECTION_ROUTE}/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: () => ["DatastoreConnection"],
    }),
    getAccessManualHook: build.query<GetAccessManualWebhookResponse, string>({
      query: (key) => ({
        url: `${CONNECTION_ROUTE}/${key}/access_manual_webhook`,
      }),
      providesTags: () => ["DatastoreConnection"],
    }),
    getAllDatastoreConnections: build.query<
      DatastoreConnectionsResponse,
      Partial<DatastoreConnectionParams>
    >({
      query: (filters) => ({
        url: CONNECTION_ROUTE + mapFiltersToSearchParams(filters),
      }),
      providesTags: () => ["DatastoreConnection"],
    }),
    getDatastoreConnectionByKey: build.query<DatastoreConnection, string>({
      query: (key) => ({
        url: `${CONNECTION_ROUTE}/${key}`,
      }),
      providesTags: (result) => [
        { type: "DatastoreConnection", id: result!.key },
      ],
      keepUnusedDataFor: 1,
    }),
    getDatasets: build.query<DatasetsReponse, string>({
      query: (key) => ({
        url: `${CONNECTION_ROUTE}/${key}/dataset`,
      }),
      providesTags: () => ["DatastoreConnection"],
    }),
    getDatastoreConnectionStatus: build.query<
      DatastoreConnectionStatus,
      string
    >({
      query: (id) => ({
        url: `${CONNECTION_ROUTE}/${id}/test`,
      }),
      providesTags: () => ["DatastoreConnection"],
      async onQueryStarted(key, { dispatch, queryFulfilled, getState }) {
        try {
          await queryFulfilled;

          const request = dispatch(
            datastoreConnectionApi.endpoints.getDatastoreConnectionByKey.initiate(
              key
            )
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
              }
            )
          );
        } catch {
          throw new Error("Error while testing connection");
        }
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
      invalidatesTags: () => ["DatastoreConnection"],
    }),
    patchDataset: build.mutation<any, PatchDatasetsRequest>({
      query: (params) => ({
        url: `${CONNECTION_ROUTE}/${params.connection_key}/dataset`,
        method: "PATCH",
        body: params.datasets,
      }),
      invalidatesTags: () => ["DatastoreConnection"],
    }),
    patchDatastoreConnection: build.mutation<
      DatastoreConnectionResponse,
      DatastoreConnectionRequest
    >({
      query: (params) => ({
        url: `${CONNECTION_ROUTE}`,
        method: "PATCH",
        body: [params],
      }),
      invalidatesTags: () => ["DatastoreConnection"],
    }),
    patchDatastoreConnections: build.mutation({
      query: ({ key, name, disabled, connection_type, access }) => ({
        url: CONNECTION_ROUTE,
        method: "PATCH",
        body: [{ key, name, disabled, connection_type, access }],
      }),
      invalidatesTags: () => ["DatastoreConnection"],
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
      invalidatesTags: () => ["DatastoreConnection"],
    }),
  }),
});

export const {
  useCreateAccessManualWebhookMutation,
  useCreateSassConnectionConfigMutation,
  useGetAccessManualHookQuery,
  useGetAllDatastoreConnectionsQuery,
  useGetDatasetsQuery,
  useGetDatastoreConnectionByKeyQuery,
  useDeleteDatastoreConnectionMutation,
  useLazyGetDatastoreConnectionStatusQuery,
  usePatchAccessManualWebhookMutation,
  usePatchDatasetMutation,
  usePatchDatastoreConnectionMutation,
  usePatchDatastoreConnectionsMutation,
  useUpdateDatastoreConnectionSecretsMutation,
} = datastoreConnectionApi;
