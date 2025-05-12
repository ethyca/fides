import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import { DataCategory } from "~/types/api";

const taxonomyApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllDataCategories: build.query<DataCategory[], void>({
      query: () => ({ url: `data_category` }),
      providesTags: () => ["Data Categories"],
      transformResponse: (categories: DataCategory[]) =>
        categories.sort((a, b) => a.fides_key.localeCompare(b.fides_key)),
    }),
    updateDataCategory: build.mutation<
      DataCategory,
      Partial<DataCategory> & Pick<DataCategory, "fides_key">
    >({
      query: (dataCategory) => ({
        url: `data_category`,
        params: { resource_type: "data_category" },
        method: "PUT",
        body: dataCategory,
      }),
      invalidatesTags: ["Data Categories"],
    }),

    createDataCategory: build.mutation<DataCategory, Partial<DataCategory>>({
      query: (dataCategory) => ({
        url: `data_category`,
        method: "POST",
        body: dataCategory,
      }),
      invalidatesTags: ["Data Categories"],
    }),

    deleteDataCategory: build.mutation<string, string>({
      query: (key) => ({
        url: `data_category/${key}`,
        params: { resource_type: "data_category" },
        method: "DELETE",
      }),
      invalidatesTags: ["Data Categories"],
    }),
  }),
});

export const {
  useGetAllDataCategoriesQuery,
  useLazyGetAllDataCategoriesQuery,
  useUpdateDataCategoryMutation,
  useDeleteDataCategoryMutation,
  useCreateDataCategoryMutation,
} = taxonomyApi;

export interface State {
  isAddFormOpen: boolean;
}

const initialState: State = {
  isAddFormOpen: false,
};

export const taxonomySlice = createSlice({
  name: "taxonomy",
  initialState,
  reducers: {
    setIsAddFormOpen: (draftState, action: PayloadAction<boolean>) => {
      draftState.isAddFormOpen = action.payload;
    },
  },
});

export const { setIsAddFormOpen } = taxonomySlice.actions;

const emptyDataCategories: DataCategory[] = [];
export const selectDataCategories: (state: RootState) => DataCategory[] =
  createSelector(
    taxonomyApi.endpoints.getAllDataCategories.select(),
    ({ data }) => data ?? emptyDataCategories,
  );

export const selectEnabledDataCategories: (state: RootState) => DataCategory[] =
  createSelector(
    taxonomyApi.endpoints.getAllDataCategories.select(),
    ({ data }) => data?.filter((dc) => dc.active) ?? emptyDataCategories,
  );

export const selectDataCategoriesMap: (
  state: RootState,
) => Map<string, DataCategory> = createSelector(
  selectDataCategories,
  (dataCategories) => new Map(dataCategories.map((dc) => [dc.fides_key, dc])),
);

const selectTaxonomy = (state: RootState) => state.taxonomy;

export const selectIsAddFormOpen = createSelector(
  selectTaxonomy,
  (state) => state.isAddFormOpen,
);

export const { reducer } = taxonomySlice;
