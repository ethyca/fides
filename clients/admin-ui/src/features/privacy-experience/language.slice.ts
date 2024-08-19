import { createSelector, createSlice } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import { Language, Page_Language_ } from "~/types/api";

interface State {
  page?: number;
  pageSize?: number;
}

const initialState: State = {
  page: 1,
  pageSize: 50,
};

interface LanguageQueryParams {
  page?: number;
  size?: number;
}

const languageApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllLanguages: build.query<Page_Language_, LanguageQueryParams>({
      query: (params) => ({
        params,
        url: `/plus/languages`,
      }),
      providesTags: () => ["Languages"],
    }),
  }),
});

export const { useGetAllLanguagesQuery } = languageApi;

export const languageSlice = createSlice({
  name: "language",
  initialState,
  reducers: {},
});

export const { reducer } = languageSlice;

const selectLanguage = (state: RootState) => state.language;

export const selectPage = createSelector(selectLanguage, (state) => state.page);

export const selectPageSize = createSelector(
  selectLanguage,
  (state) => state.pageSize,
);

const emptyLanguages: Language[] = [];
export const selectAllLanguages = createSelector(
  [(RootState) => RootState, selectPage, selectPageSize],
  (RootState, page, pageSize) => {
    const data = languageApi.endpoints.getAllLanguages.select({
      page,
      size: pageSize,
    })(RootState)?.data;
    return data ? data.items : emptyLanguages;
  },
);
