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

const DEFAULT_PAGE_SIZE = 100;

// Helpers
const mapFiltersToSearchParams = ({
  search,
  system_type,
  page,
  size,
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
  if (page) {
    queryString += queryString ? `&page=${page}` : `page=${page}`;
  }
  if (size) {
    queryString += queryString ? `&size=${size}` : `size=${size}`;
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
      async queryFn(filters, api, extraOptions, baseQuery) {
        const firstPage = await baseQuery({
          url: `${CONNECTION_TYPE_ROUTE}${mapFiltersToSearchParams({ ...filters, page: 1, size: DEFAULT_PAGE_SIZE })}`,
        });

        if (firstPage.error) {
          return { error: firstPage.error };
        }

        const data = firstPage.data as Page_ConnectionSystemTypeMap_;
        const totalPages = data.pages ?? 1;

        if (totalPages <= 1) {
          return { data };
        }

        // Fetch remaining pages in parallel
        const remainingPages = await Promise.all(
          Array.from({ length: totalPages - 1 }, (_, i) =>
            baseQuery({
              url: `${CONNECTION_TYPE_ROUTE}${mapFiltersToSearchParams({
                ...filters,
                // i starts at 0, and we already fetched page 1, so add 2 to get page 2, 3, etc.
                page: i + 2,
                size: DEFAULT_PAGE_SIZE,
              })}`,
            }),
          ),
        );

        // Combine all results
        const allItems = [
          ...data.items,
          ...remainingPages.flatMap(
            (page) => (page.data as Page_ConnectionSystemTypeMap_).items,
          ),
        ];

        return {
          data: {
            ...data,
            items: allItems,
            page: 1,
            size: allItems.length,
            total: allItems.length,
            pages: 1,
          },
        };
      },
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
