import { createSelector, createSlice } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import type { RootState } from "~/app/store";
import { selectToken } from "~/features/auth";
import { addCommonHeaders } from "~/features/common/CommonHeaders";
import { DataUse } from "~/types/api";

export const dataUseApi = createApi({
  reducerPath: "dataUseApi",
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_FIDESCTL_API,
    prepareHeaders: (headers, { getState }) => {
      const token: string | null = selectToken(getState() as RootState);
      addCommonHeaders(headers, token);
      return headers;
    },
  }),
  tagTypes: ["Data Uses"],
  endpoints: (build) => ({
    getAllDataUses: build.query<DataUse[], void>({
      query: () => ({ url: `data_use/` }),
      providesTags: () => ["Data Uses"],
      transformResponse: (uses: DataUse[]) =>
        uses.sort((a, b) => a.fides_key.localeCompare(b.fides_key)),
    }),
    getDataUseByKey: build.query<DataUse, string>({
      query: (fidesKey) => ({ url: `data_use/${fidesKey}` }),
    }),
    updateDataUse: build.mutation<
      DataUse,
      Partial<DataUse> & Pick<DataUse, "fides_key">
    >({
      query: (dataUse) => ({
        url: `data_use/`,
        params: { resource_type: "data_use" },
        method: "PUT",
        body: dataUse,
      }),
      invalidatesTags: ["Data Uses"],
    }),
    createDataUse: build.mutation<DataUse, DataUse>({
      query: (dataUse) => ({
        url: `data_use/`,
        method: "POST",
        body: dataUse,
      }),
      invalidatesTags: ["Data Uses"],
    }),
    deleteDataUse: build.mutation<string, string>({
      query: (key) => ({
        url: `data_use/${key}`,
        params: { resource_type: "data_use" },
        method: "DELETE",
      }),
      invalidatesTags: ["Data Uses"],
    }),
  }),
});

export const {
  useGetAllDataUsesQuery,
  useGetDataUseByKeyQuery,
  useUpdateDataUseMutation,
  useCreateDataUseMutation,
  useDeleteDataUseMutation,
} = dataUseApi;

export interface State {}
const initialState: State = {};

export const dataUseSlice = createSlice({
  name: "dataUse",
  initialState,
  reducers: {},
});

export const { reducer } = dataUseSlice;

const emptyDataUses: DataUse[] = [];
export const selectDataUses: (state: RootState) => DataUse[] = createSelector(
  dataUseApi.endpoints.getAllDataUses.select(),
  ({ data }) => data ?? emptyDataUses
);
