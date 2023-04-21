import { createSelector, createSlice } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import { DataQualifier } from "~/types/api";

const dataQualifierApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllDataQualifiers: build.query<DataQualifier[], void>({
      query: () => ({ url: `data_qualifier/` }),
      providesTags: () => ["Data Qualifiers"],
      transformResponse: (qualifiers: DataQualifier[]) =>
        qualifiers.sort((a, b) => a.fides_key.localeCompare(b.fides_key)),
    }),

    updateDataQualifier: build.mutation<
      DataQualifier,
      Partial<DataQualifier> & Pick<DataQualifier, "fides_key">
    >({
      query: (dataQualifier) => ({
        url: `data_qualifier/`,
        params: { resource_type: "data_qualifier" },
        method: "PUT",
        body: dataQualifier,
      }),
      invalidatesTags: ["Data Qualifiers"],
    }),
    createDataQualifier: build.mutation<DataQualifier, DataQualifier>({
      query: (dataQualifier) => ({
        url: `data_qualifier/`,
        method: "POST",
        body: dataQualifier,
      }),
      invalidatesTags: ["Data Qualifiers"],
    }),
    deleteDataQualifier: build.mutation<string, string>({
      query: (key) => ({
        url: `data_qualifier/${key}`,
        params: { resource_type: "data_qualifier" },
        method: "DELETE",
      }),
      invalidatesTags: ["Data Qualifiers"],
    }),
  }),
});

export const {
  useGetAllDataQualifiersQuery,
  useUpdateDataQualifierMutation,
  useCreateDataQualifierMutation,
  useDeleteDataQualifierMutation,
} = dataQualifierApi;

export interface State {}
const initialState: State = {};

export const dataQualifierSlice = createSlice({
  name: "dataQualifier",
  initialState,
  reducers: {},
});

export const { reducer } = dataQualifierSlice;

const emptyDataQualifiers: DataQualifier[] = [];
export const selectDataQualifiers: (state: RootState) => DataQualifier[] =
  createSelector(
    dataQualifierApi.endpoints.getAllDataQualifiers.select(),
    ({ data }) => data ?? emptyDataQualifiers
  );
