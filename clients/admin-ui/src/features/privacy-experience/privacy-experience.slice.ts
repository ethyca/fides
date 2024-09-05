import { createSelector, createSlice } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import {
  ExperienceConfigCreate,
  ExperienceConfigDisabledUpdate,
  ExperienceConfigListViewResponse,
  ExperienceConfigResponse,
  ExperienceConfigUpdate,
  ExperienceTranslation,
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
  | "purpose_header"
  | "privacy_policy_link_label"
  | "privacy_policy_url"
  | "modal_link_label";
export type ExperienceConfigUpdateParams = Omit<
  Partial<ExperienceConfigUpdate>,
  ExperienceConfigOptionalFields
> & {
  id: string;
  banner_title?: string | null;
  banner_description?: string | null;
  purpose_header?: string | null;
  privacy_policy_link_label?: string | null;
  privacy_policy_url?: string | null;
  modal_link_label?: string | null;
};
type ExperienceConfigEnableDisableParams = ExperienceConfigDisabledUpdate & {
  id: string;
};
export type ExperienceConfigCreateParams = Omit<
  Partial<ExperienceConfigCreate>,
  ExperienceConfigOptionalFields
> & {
  banner_title?: string | null;
  banner_description?: string | null;
  purpose_header?: string | null;
  privacy_policy_link_label?: string | null;
  privacy_policy_url?: string | null;
  modal_link_label?: string | null;
};

const privacyExperienceConfigApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllExperienceConfigs: build.query<
      Page_ExperienceConfigListViewResponse_,
      ExperienceConfigParams
    >({
      query: (params) => ({
        url: `experience-config`,
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
      invalidatesTags: () => ["Privacy Experience Configs", "Property"],
    }),
    limitedPatchExperienceConfig: build.mutation<
      ExperienceConfigResponse,
      ExperienceConfigEnableDisableParams
    >({
      query: ({ id, disabled }) => ({
        method: "PATCH",
        url: `experience-config/${id}/limited_update`,
        body: { disabled },
      }),
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
    getAvailableConfigTranslations: build.query<
      Array<ExperienceTranslation>,
      string
    >({
      query: (id) => ({
        url: `experience-config/${id}/available_translations`,
      }),
      providesTags: () => ["Experience Config Translations"],
    }),
    postExperienceConfig: build.mutation<
      ExperienceConfigResponse,
      ExperienceConfigCreate
    >({
      query: (payload) => ({
        method: "POST",
        url: `experience-config`,
        body: payload,
      }),
      invalidatesTags: () => ["Privacy Experience Configs", "Property"],
    }),
  }),
});

export const {
  useGetAllExperienceConfigsQuery,
  usePatchExperienceConfigMutation,
  useLimitedPatchExperienceConfigMutation,
  useGetExperienceConfigByIdQuery,
  useGetAvailableConfigTranslationsQuery,
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
  (state) => state.page,
);

export const selectPageSize = createSelector(
  selectPrivacyExperienceConfig,
  (state) => state.pageSize,
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
  },
);
