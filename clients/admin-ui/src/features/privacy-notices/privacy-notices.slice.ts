import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import {
  Page_PrivacyNoticeResponse_,
  PrivacyNoticeRegion,
  PrivacyNoticeResponse,
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

interface PrivacyNoticesParams {
  show_disabled?: boolean;
  region?: PrivacyNoticeRegion;
  systems_applicable?: boolean;
  page?: number;
  size?: number;
}

const privacyNoticesApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllPrivacyNotices: build.query<
      Page_PrivacyNoticeResponse_,
      PrivacyNoticesParams
    >({
      query: (params) => ({
        url: `privacy-notice/`,
        params: { ...params, systems_applicable: true, show_disabled: true },
      }),
      providesTags: () => ["PrivacyNotices"],
    }),
  }),
});

export const { useGetAllPrivacyNoticesQuery } = privacyNoticesApi;

export const privacyNoticesSlice = createSlice({
  name: "privacyNotices",
  initialState,
  reducers: {
    setActivePrivacyNoticeId: (
      draftState,
      action: PayloadAction<string | undefined>
    ) => {
      draftState.activePrivacyNoticeId = action.payload;
    },
  },
});

export const { setActivePrivacyNoticeId } = privacyNoticesSlice.actions;

export const { reducer } = privacyNoticesSlice;

const selectPrivacyNotices = (state: RootState) => state.privacyNotices;
export const selectPage = createSelector(
  selectPrivacyNotices,
  (state) => state.page
);

export const selectPageSize = createSelector(
  selectPrivacyNotices,
  (state) => state.pageSize
);

const emptyPrivacyNotices: PrivacyNoticeResponse[] = [];
export const selectAllPrivacyNotices = createSelector(
  [(RootState) => RootState, selectPage, selectPageSize],
  (RootState, page, pageSize) => {
    const data = privacyNoticesApi.endpoints.getAllPrivacyNotices.select({
      page,
      size: pageSize,
    })(RootState)?.data;
    return data ? data.items : emptyPrivacyNotices;
  }
);
