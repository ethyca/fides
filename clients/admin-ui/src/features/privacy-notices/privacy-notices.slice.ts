import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import {
  LimitedPrivacyNoticeResponseSchema,
  Page_LimitedPrivacyNoticeResponseSchema_,
  PrivacyNoticeCreation,
  PrivacyNoticeRegion,
  PrivacyNoticeResponse,
  PrivacyNoticeUpdate,
} from "~/types/api";

export interface State {
  activePrivacyNoticeId?: string;
  page?: number;
  pageSize?: number;
}

const initialState: State = {
  page: 1,
  pageSize: 50,
};

interface PrivacyNoticesParams {
  show_disabled?: boolean;
  region?: PrivacyNoticeRegion;
  systems_applicable?: boolean;
  filter_by_framework?: boolean;
  page?: number;
  size?: number;
}

type PrivacyNoticeUpdateParams = PrivacyNoticeUpdate & { id: string };

const privacyNoticesApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllPrivacyNotices: build.query<
      Page_LimitedPrivacyNoticeResponseSchema_,
      PrivacyNoticesParams
    >({
      query: (params) => ({
        url: `privacy-notice/`,
        params: { ...params, show_disabled: true },
      }),
      providesTags: () => ["Privacy Notices"],
    }),
    patchPrivacyNotices: build.mutation<
      PrivacyNoticeResponse[],
      PrivacyNoticeUpdateParams
    >({
      query: (payload) => {
        const { id, ...body } = payload;
        return {
          method: "PATCH",
          url: `privacy-notice/${id}`,
          params: { id },
          body,
        };
      },
      invalidatesTags: () => ["Privacy Notices"],
    }),
    getPrivacyNoticeById: build.query<PrivacyNoticeResponse, string>({
      query: (id) => ({
        url: `privacy-notice/${id}`,
      }),
      providesTags: (result, error, arg) => [
        { type: "Privacy Notices", id: arg },
      ],
    }),
    postPrivacyNotice: build.mutation<
      PrivacyNoticeResponse[],
      PrivacyNoticeCreation
    >({
      query: (payload) => ({
        method: "POST",
        url: `privacy-notice/`,
        body: payload,
      }),
      invalidatesTags: () => ["Privacy Notices"],
    }),
  }),
});

export const {
  useGetAllPrivacyNoticesQuery,
  usePatchPrivacyNoticesMutation,
  useGetPrivacyNoticeByIdQuery,
  usePostPrivacyNoticeMutation,
} = privacyNoticesApi;

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

const emptyPrivacyNotices: LimitedPrivacyNoticeResponseSchema[] = [];
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
