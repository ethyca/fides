import { createSelector, createSlice } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import {
  ExperienceConfigCreate,
  ExperienceConfigListViewResponse,
  ExperienceConfigResponse,
  ExperienceConfigUpdate,
  Page_ExperienceConfigListViewResponse_,
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

// Construct custom types that allows the optional fields on
// PrivacyExperienceConfig API requests to be *truly* nullable
// (see // https://github.com/ethyca/fides/issues/1169)
type ExperienceConfigOptionalFields =
  | "banner_title"
  | "banner_description"
  | "privacy_policy_link_label"
  | "privacy_policy_url";
export type ExperienceConfigUpdateParams = Omit<
  Partial<ExperienceConfigUpdate>,
  ExperienceConfigOptionalFields
> & {
  id: string;
  banner_title?: string | null;
  banner_description?: string | null;
  privacy_policy_link_label?: string | null;
  privacy_policy_url?: string | null;
};
export type ExperienceConfigCreateParams = Omit<
  Partial<ExperienceConfigCreate>,
  ExperienceConfigOptionalFields
> & {
  banner_title?: string | null;
  banner_description?: string | null;
  privacy_policy_link_label?: string | null;
  privacy_policy_url?: string | null;
};

const privacyExperienceConfigApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllExperienceConfigs: build.query<
      Page_ExperienceConfigListViewResponse_,
      ExperienceConfigParams
    >({
      query: (params) => ({
        url: `experience-config/`,
        params: { ...params, show_disabled: true },
      }),
      providesTags: () => ["Privacy Experience Configs"],
    }),
    patchExperienceConfig: build.mutation<
      ExperienceConfigResponse,
      ExperienceConfigUpdateParams
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
      ExperienceConfigResponse,
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

const emptyExperienceConfigs: ExperienceConfigListViewResponse[] = [];
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
