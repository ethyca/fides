import { createSelector, createSlice } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import {
  Page_PrivacyExperienceResponse_,
  PrivacyExperienceResponse,
  PrivacyNoticeRegion,
} from "~/types/api";

export interface State {
  activePrivacyNoticeId?: string;
  page?: number;
  pageSize?: number;
}

const initialState: State = {
  page: 1,
  pageSize: 10,
};

interface PrivacyExperienceParams {
  show_disabled?: boolean;
  region?: PrivacyNoticeRegion;
  page?: number;
  size?: number;
}

const privacyExperienceApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllPrivacyExperiences: build.query<
      Page_PrivacyExperienceResponse_,
      PrivacyExperienceParams
    >({
      query: (params) => ({
        url: `privacy-experience/`,
        params: { ...params, show_disabled: true },
      }),
      providesTags: () => ["Privacy Experiences"],
    }),
  }),
});

export const { useGetAllPrivacyExperiencesQuery } = privacyExperienceApi;

export const privacyExperienceSlice = createSlice({
  name: "privacyExperience",
  initialState,
  reducers: {},
});

export const { reducer } = privacyExperienceSlice;

const selectPrivacyExperiences = (state: RootState) => state.privacyExperience;
export const selectPage = createSelector(
  selectPrivacyExperiences,
  (state) => state.page
);

export const selectPageSize = createSelector(
  selectPrivacyExperiences,
  (state) => state.pageSize
);

const emptyPrivacyNotices: PrivacyExperienceResponse[] = [];
export const selectAllPrivacyExperiences = createSelector(
  [(RootState) => RootState, selectPage, selectPageSize],
  (RootState, page, pageSize) => {
    const data = privacyExperienceApi.endpoints.getAllPrivacyExperiences.select(
      {
        page,
        size: pageSize,
      }
    )(RootState)?.data;
    return data ? data.items : emptyPrivacyNotices;
  }
);
