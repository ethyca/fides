import { createSelector, createSlice } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import {
  ExperienceConfigCreate,
  ExperienceConfigCreateOrUpdateResponse,
  ExperienceConfigResponse,
  ExperienceConfigUpdate,
  Page_ExperienceConfigResponse_,
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

interface ExperienceConfigParams {
  show_disabled?: boolean;
  region?: PrivacyNoticeRegion;
  page?: number;
  size?: number;
}

const privacyExperienceConfigApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllExperienceConfigs: build.query<
      Page_ExperienceConfigResponse_,
      ExperienceConfigParams
    >({
      query: (params) => ({
        url: `experience-config/`,
        params: { ...params, show_disabled: true },
      }),
      providesTags: () => ["Privacy Experience Configs"],
    }),
    patchExperienceConfig: build.mutation<
      ExperienceConfigCreateOrUpdateResponse,
      // Regions is required
      Partial<ExperienceConfigUpdate> &
        Pick<ExperienceConfigResponse, "id" | "regions">
    >({
      query: (payload) => {
        const { id, ...body } = payload;
        return {
          method: "PATCH",
          url: `experience-config/${id}`,
          body,
        };
      },
      invalidatesTags: () => ["Privacy Experience Configs"],
    }),
    getExperienceConfigById: build.query<ExperienceConfigResponse, string>({
      query: (id) => ({
        url: `experience-config/${id}`,
      }),
      providesTags: (result, error, arg) => [
        { type: "Privacy Experience Configs", id: arg },
      ],
    }),
    postExperienceConfig: build.mutation<
      ExperienceConfigCreateOrUpdateResponse,
      ExperienceConfigCreate
    >({
      query: (payload) => ({
        method: "POST",
        url: `experience-config/`,
        body: payload,
      }),
      invalidatesTags: () => ["Privacy Experience Configs"],
    }),
  }),
});

export const {
  useGetAllExperienceConfigsQuery,
  usePatchExperienceConfigMutation,
  useGetExperienceConfigByIdQuery,
  usePostExperienceConfigMutation,
} = privacyExperienceConfigApi;

export const privacyExperienceConfigSlice = createSlice({
  name: "privacyExperienceConfig",
  initialState,
  reducers: {},
});

export const { reducer } = privacyExperienceConfigSlice;

const selectPrivacyExperienceConfig = (state: RootState) =>
  state.privacyExperienceConfig;
export const selectPage = createSelector(
  selectPrivacyExperienceConfig,
  (state) => state.page
);

export const selectPageSize = createSelector(
  selectPrivacyExperienceConfig,
  (state) => state.pageSize
);

const emptyExperienceConfigs: ExperienceConfigResponse[] = [];
export const selectAllExperienceConfigs = createSelector(
  [(RootState) => RootState, selectPage, selectPageSize],
  (RootState, page, pageSize) => {
    const data =
      privacyExperienceConfigApi.endpoints.getAllExperienceConfigs.select({
        page,
        size: pageSize,
      })(RootState)?.data;
    return data ? data.items : emptyExperienceConfigs;
  }
);
