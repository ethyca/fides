import { createSelector, createSlice } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import { DataUse } from "~/types/api";

const dataUseApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllDataUses: build.query<DataUse[], void>({
      query: () => ({ url: `data_use` }),
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
        url: `data_use`,
        params: { resource_type: "data_use" },
        method: "PUT",
        body: dataUse,
      }),
      invalidatesTags: ["Data Uses"],
    }),
    createDataUse: build.mutation<DataUse, DataUse>({
      query: (dataUse) => ({
        url: `data_use`,
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
  useLazyGetAllDataUsesQuery,
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
  [(RootState) => RootState, dataUseApi.endpoints.getAllDataUses.select()],
  (RootState, { data }) => data ?? emptyDataUses,
);

export const selectDataUsesMap = createSelector(
  selectDataUses,
  (dataUses) => new Map(dataUses.map((dataUse) => [dataUse.name, dataUse])),
);

export const selectDataUseOptions = createSelector(selectDataUses, (dataUses) =>
  dataUses.map((du) => ({
    label: du.name ?? du.fides_key,
    value: du.fides_key,
    description: du.description,
  })),
);

export const selectEnabledDataUses = createSelector(
  selectDataUses,
  (dataUses) => dataUses.filter((du) => du.active),
);

export const selectEnabledDataUseOptions = createSelector(
  selectDataUses,
  (dataUses) =>
    dataUses
      .filter((du) => du.active)
      .map((du) => ({
        label: du.fides_key,
        value: du.fides_key,
      })),
);
