import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import {
  Page_TCFConfigurationResponse_,
  Page_TCFPublisherRestrictionResponse_,
  TCFConfigurationDetail,
  TCFConfigurationRequest,
  TCFPublisherRestrictionRequest,
} from "~/types/api";
import { PaginationQueryParams } from "~/types/common/PaginationQueryParams";

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
    getPublisherRestrictions: build.query<
      Page_TCFPublisherRestrictionResponse_,
      {
        configuration_id: string;
        purpose_id: number;
      } & Partial<PaginationQueryParams>
    >({
      query: ({ configuration_id, purpose_id, ...params }) => ({
        url: `/plus/tcf/configurations/${configuration_id}/publisher_restrictions`,
        params: { purpose_id, ...params },
      }),
      providesTags: (_result, _error, { configuration_id }) => [
        { type: "TCF Purpose Override", id: configuration_id },
      ],
    }),
    getTCFConfigurations: build.query<
      Page_TCFConfigurationResponse_,
      Partial<PaginationQueryParams>
    >({
      query: (params) => ({
        url: "/plus/tcf/configurations",
        params,
      }),
      providesTags: () => ["TCF Purpose Override"],
    }),
    getTCFConfiguration: build.query<TCFConfigurationDetail, string>({
      query: (configuration_id) => ({
        url: `/plus/tcf/configurations/${configuration_id}`,
      }),
      providesTags: (_result, _error, configuration_id) => [
        { type: "TCF Purpose Override", id: configuration_id },
      ],
    }),
    createTCFConfiguration: build.mutation<
      TCFConfigurationDetail,
      TCFConfigurationRequest
    >({
      query: (body) => ({
        url: "/plus/tcf/configurations",
        method: "POST",
        body,
      }),
      invalidatesTags: () => ["TCF Purpose Override"],
    }),
    deleteTCFConfiguration: build.mutation<void, string>({
      query: (configuration_id) => ({
        url: `/plus/tcf/configurations/${configuration_id}`,
        method: "DELETE",
      }),
      invalidatesTags: () => ["TCF Purpose Override"],
    }),
    createPublisherRestriction: build.mutation<
      void,
      { configuration_id: string; restriction: TCFPublisherRestrictionRequest }
    >({
      query: ({ configuration_id, restriction }) => ({
        url: `/plus/tcf/configurations/${configuration_id}/publisher_restrictions`,
        method: "POST",
        body: restriction,
      }),
      invalidatesTags: (_result, _error, { configuration_id }) => [
        { type: "TCF Purpose Override", id: configuration_id },
      ],
    }),
    updatePublisherRestriction: build.mutation<
      void,
      {
        configuration_id: string;
        restriction_id: string;
        restriction: TCFPublisherRestrictionRequest;
      }
    >({
      query: ({ configuration_id, restriction_id, restriction }) => ({
        url: `/plus/tcf/configurations/${configuration_id}/publisher_restrictions/${restriction_id}`,
        method: "PATCH",
        body: restriction,
      }),
      invalidatesTags: (_result, _error, { configuration_id }) => [
        { type: "TCF Purpose Override", id: configuration_id },
      ],
    }),
  }),
});

export const {
  useGetPublisherRestrictionsQuery,
  useGetTCFConfigurationsQuery,
  useGetTCFConfigurationQuery,
  useCreateTCFConfigurationMutation,
  useDeleteTCFConfigurationMutation,
  useCreatePublisherRestrictionMutation,
  useUpdatePublisherRestrictionMutation,
} = tcfConfigApi;

export default tcfConfigSlice.reducer;
