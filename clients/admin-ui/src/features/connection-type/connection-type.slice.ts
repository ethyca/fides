import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/dist/query/react";
import { addCommonHeaders } from "common/CommonHeaders";
import { STEPS } from "datastore-connections/add-connection/constants";
import { AddConnectionStep } from "datastore-connections/add-connection/types";
import { SystemType } from "datastore-connections/constants";
import { DatastoreConnection } from "datastore-connections/types";

import type { RootState } from "../../app/store";
import { BASE_URL, CONNECTION_TYPE_ROUTE } from "../../constants";
import { selectToken } from "../auth";
import {
  AllConnectionTypesResponse,
  ConnectionOption,
  ConnectionTypeParams,
  ConnectionTypeSecretSchemaReponse,
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
  search: "",
  step: STEPS.find((step) => step.stepId === 1)!,
  system_type: undefined,
};

export const connectionTypeSlice = createSlice({
  name: "connectionType",
  initialState,
  reducers: {
    setConnection: (
      state,
      action: PayloadAction<DatastoreConnection | undefined>
    ) => ({
      ...state,
      connection: action.payload,
    }),
    setConnectionOption: (
      state,
      action: PayloadAction<ConnectionOption | undefined>
    ) => ({
      ...state,
      connectionOption: action.payload,
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
  setConnection,
  setConnectionOption,
  setSearch,
  setStep,
  setSystemType,
} = connectionTypeSlice.actions;

export const { reducer } = connectionTypeSlice;

export const selectConnectionTypeState = (state: RootState) =>
  state.connectionType;
export const selectConnectionTypeFilters = (
  state: RootState
): ConnectionTypeParams => ({
  search: state.connectionType.search,
  system_type: state.connectionType.system_type,
});

export const connectionTypeApi = createApi({
  reducerPath: "connectionTypeApi",
  baseQuery: fetchBaseQuery({
    baseUrl: BASE_URL,
    prepareHeaders: (headers, { getState }) => {
      const token: string | null = selectToken(getState() as RootState);
      addCommonHeaders(headers, token);
      return headers;
    },
  }),
  tagTypes: ["ConnectionType"],
  endpoints: (build) => ({
    getAllConnectionTypes: build.query<
      AllConnectionTypesResponse,
      Partial<ConnectionTypeParams>
    >({
      query: (filters) => ({
        url: `${CONNECTION_TYPE_ROUTE}${mapFiltersToSearchParams(filters)}`,
      }),
      providesTags: () => ["ConnectionType"],
    }),
    getConnectionTypeSecretSchema: build.query<
      ConnectionTypeSecretSchemaReponse,
      string
    >({
      query: (connectionType) => ({
        url: `${CONNECTION_TYPE_ROUTE}/${connectionType}/secret`,
      }),
      providesTags: () => ["ConnectionType"],
    }),
  }),
});

export const {
  useGetAllConnectionTypesQuery,
  useGetConnectionTypeSecretSchemaQuery,
} = connectionTypeApi;
