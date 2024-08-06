import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { STEPS } from "datastore-connections/add-connection/constants";
import { AddConnectionStep } from "datastore-connections/add-connection/types";

import { CONNECTION_TYPE_ROUTE } from "~/constants";
import { baseApi } from "~/features/common/api.slice";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  Page_ConnectionSystemTypeMap_,
  SystemType,
} from "~/types/api";

import type { RootState } from "../../app/store";
import {
  ConnectionTypeParams,
  ConnectionTypeSecretSchemaResponse,
  ConnectionTypeState,
} from "./types";

// Helpers
const mapFiltersToSearchParams = ({
  search,
  system_type,
}: Partial<ConnectionTypeParams>): string => {
  let queryString = "";
  if (search) {
    queryString += queryString ? `&search=${search}` : `search=${search}`;
  }
  if (system_type) {
    queryString += queryString
      ? `&system_type=${system_type}`
      : `system_type=${system_type}`;
  }
  return queryString ? `?${queryString}` : "";
};

const initialState: ConnectionTypeState = {
  connection: undefined,
  connectionOption: undefined,
  connectionOptions: [],
  search: "",
  step: STEPS.find((step) => step.stepId === 1)!,
  system_type: undefined,
};

export const connectionTypeSlice = createSlice({
  name: "connectionType",
  initialState,
  reducers: {
    reset: () => initialState,
    setConnection: (
      state,
      action: PayloadAction<ConnectionConfigurationResponse | undefined>,
    ) => ({
      ...state,
      connection: action.payload,
    }),
    setConnectionOption: (
      state,
      action: PayloadAction<ConnectionSystemTypeMap | undefined>,
    ) => ({
      ...state,
      connectionOption: action.payload,
    }),
    setConnectionOptions: (
      state,
      action: PayloadAction<ConnectionSystemTypeMap[]>,
    ) => ({
      ...state,
      connectionOptions: action.payload,
    }),
    setSearch: (state, action: PayloadAction<string>) => ({
      ...state,
      search: action.payload,
    }),
    setStep: (state, action: PayloadAction<AddConnectionStep>) => ({
      ...state,
      step: action.payload,
    }),
    setSystemType: (state, action: PayloadAction<SystemType | string>) => ({
      ...state,
      system_type: action.payload as SystemType,
    }),
  },
});

export const {
  reset,
  setConnection,
  setConnectionOption,
  setConnectionOptions,
  setSearch,
  setStep,
  setSystemType,
} = connectionTypeSlice.actions;

export const { reducer } = connectionTypeSlice;

export const selectConnectionTypeState = (state: RootState) =>
  state.connectionType;
export const selectConnectionTypeFilters = (
  state: RootState,
): ConnectionTypeParams => ({
  search: state.connectionType.search,
  system_type: state.connectionType.system_type,
});

export const connectionTypeApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllConnectionTypes: build.query<
      Page_ConnectionSystemTypeMap_,
      Partial<ConnectionTypeParams>
    >({
      query: (filters) => ({
        url: `${CONNECTION_TYPE_ROUTE}${mapFiltersToSearchParams(filters)}`,
      }),
      providesTags: () => ["Connection Type"],
    }),
    getConnectionTypeSecretSchema: build.query<
      ConnectionTypeSecretSchemaResponse,
      string
    >({
      query: (connectionType) => ({
        url: `${CONNECTION_TYPE_ROUTE}/${connectionType}/secret`,
      }),
      providesTags: () => ["Connection Type"],
    }),
  }),
});

export const {
  useGetAllConnectionTypesQuery,
  useGetConnectionTypeSecretSchemaQuery,
} = connectionTypeApi;

export const selectConnectionTypes = createSelector(
  [
    (RootState) => RootState,
    connectionTypeApi.endpoints.getAllConnectionTypes.select({
      search: "",
    }),
  ],
  (RootState, { data }) => data?.items ?? [],
);
