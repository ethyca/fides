import { createSelector, createSlice } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import {
  Page_PrivacyExperienceResponse_,
  PrivacyExperience,
  PrivacyExperienceResponse,
  PrivacyNoticeRegion,
} from "~/types/api";

export interface State {
  page?: number;
  pageSize?: number;
}

const initialState: State = {
  page: 1,
  pageSize: 50,
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
    patchPrivacyExperience: build.mutation<
      PrivacyExperienceResponse[],
      Partial<PrivacyExperienceResponse>[]
    >({
      query: (payload) => ({
        method: "PATCH",
        url: `privacy-experience/`,
        body: payload,
      }),
      invalidatesTags: () => ["Privacy Experiences"],
    }),
    getPrivacyExperienceById: build.query<PrivacyExperienceResponse, string>({
      query: (id) => ({
        url: `privacy-experience/${id}`,
      }),
      providesTags: (result, error, arg) => [
        { type: "Privacy Experiences", id: arg },
      ],
    }),
    postPrivacyExperience: build.mutation<PrivacyExperience[], void>({
      query: (payload) => ({
        method: "POST",
        url: `privacy-experience/`,
        body: payload,
      }),
      invalidatesTags: () => ["Privacy Experiences"],
    }),
  }),
});

export const {
  useGetAllPrivacyExperiencesQuery,
  usePatchPrivacyExperienceMutation,
  useGetPrivacyExperienceByIdQuery,
  usePostPrivacyExperienceMutation,
} = privacyExperienceApi;

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

const emptyPrivacyExperiences: PrivacyExperienceResponse[] = [];
export const selectAllPrivacyExperiences = createSelector(
  [(RootState) => RootState, selectPage, selectPageSize],
  (RootState, page, pageSize) => {
    const data = privacyExperienceApi.endpoints.getAllPrivacyExperiences.select(
      {
        page,
        size: pageSize,
      }
    )(RootState)?.data;
    return data ? data.items : emptyPrivacyExperiences;
  }
);
