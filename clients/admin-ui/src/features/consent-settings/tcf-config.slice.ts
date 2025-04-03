import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import {
  PaginatedResponse,
  PaginationQueryParams,
} from "~/types/common/PaginationQueryParams";

export interface TCFConfiguration {
  id: string;
  name: string;
}

interface CreateTCFConfigurationRequest {
  name: string;
}

export interface State {
  page: number;
  pageSize: number;
}

const initialState: State = {
  page: 1,
  pageSize: 50,
};

export const tcfConfigSlice = createSlice({
  name: "tcfConfig",
  initialState,
  reducers: {
    setPage: (state, action: PayloadAction<number>) => ({
      ...state,
      page: action.payload,
    }),
    setPageSize: (state, action: PayloadAction<number>) => ({
      ...state,
      page: initialState.page, // Reset to first page when changing page size
      pageSize: action.payload,
    }),
  },
});

export const { setPage, setPageSize } = tcfConfigSlice.actions;

// Selectors
export const selectTCFConfigState = (state: RootState) =>
  state[tcfConfigSlice.name];

export const selectTCFConfigFilters = createSelector(
  selectTCFConfigState,
  (state): PaginationQueryParams => ({
    page: state?.page ?? initialState.page,
    size: state?.pageSize ?? initialState.pageSize,
  }),
);

// TCF configurations API
export const tcfConfigApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getTCFConfigurations: build.query<
      PaginatedResponse<TCFConfiguration>,
      Partial<PaginationQueryParams>
    >({
      query: (params) => ({
        url: "/plus/tcf/configurations",
        params,
      }),
      providesTags: () => ["TCF Purpose Override"],
    }),
    createTCFConfiguration: build.mutation<
      TCFConfiguration,
      CreateTCFConfigurationRequest
    >({
      query: (body) => ({
        url: "/plus/tcf/configurations",
        method: "POST",
        body,
      }),
      invalidatesTags: () => ["TCF Purpose Override"],
    }),
  }),
});

export const {
  useGetTCFConfigurationsQuery,
  useCreateTCFConfigurationMutation,
} = tcfConfigApi;

export default tcfConfigSlice.reducer;
