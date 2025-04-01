import { createSelector } from "@reduxjs/toolkit";

import { baseApi } from "~/features/common/api.slice";
// Import the types needed for the patchConfigurationSettings mutation
import {
  MessagingConfigResponse,
  StorageConfigResponse,
} from "~/features/privacy-requests/types";
import {
  PlusApplicationConfig as ApplicationConfig,
  PrivacyExperienceGPPSettings,
  SecurityApplicationConfig,
} from "~/types/api";
import { PlusConsentSettingsApplicationConfig } from "~/types/api/models/PlusConsentSettingsApplicationConfig";

import type { RootState } from "../../app/store";

// Config Settings API
export const configSettingsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getConfigurationSettings: build.query<
      Record<string, any>,
      { api_set: boolean }
    >({
      query: ({ api_set }) => ({
        url: `/config`,
        method: "GET",
        params: { api_set },
      }),
      providesTags: ["Configuration Settings"],
    }),
    putConfigurationSettings: build.mutation<
      ApplicationConfig,
      ApplicationConfig
    >({
      query: (params) => ({
        url: `/config`,
        method: "PUT",
        body: params,
      }),
      invalidatesTags: ["Configuration Settings"],
    }),
    patchConfigurationSettings: build.mutation<
      any,
      | ApplicationConfig
      | MessagingConfigResponse
      | StorageConfigResponse
      | SecurityApplicationConfig
    >({
      query: (params) => ({
        url: `/config`,
        method: "PATCH",
        body: params,
      }),
      // Switching GPP settings causes the backend to update privacy notices behind the scenes, so
      // invalidate privacy notices when a patch goes through.
      invalidatesTags: ["Configuration Settings", "Privacy Notices"],
    }),
  }),
});

export const {
  useGetConfigurationSettingsQuery,
  usePutConfigurationSettingsMutation,
  usePatchConfigurationSettingsMutation,
} = configSettingsApi;

export type CORSOrigins = Pick<SecurityApplicationConfig, "cors_origins">;
/**
 * NOTE:
 * 1. "configSet" stores the results from `/api/v1/config?api_set=false`, and
 *    contains the config settings that are set exclusively on the server via
 *    TOML/ENV configuration.
 * 2. "apiSet" stores the results from `/api/v1/config?api_set=true`, and
 *    are the config settings that we can read/write via the API.
 *
 * These two settings are merged together at runtime by Fides when enforcing
 * CORS origins, and although they're awkwardly-named concepts (try saying
 * "config set config settings" 10 times fast), we're mirroring the API here to
 * be consistent!
 */
export type CORSOriginsSettings = {
  configSet: SecurityApplicationConfig & { cors_origin_regex?: string };
  apiSet: SecurityApplicationConfig;
};

export const selectCORSOrigins: (state: RootState) => CORSOriginsSettings =
  createSelector(
    [
      (state) => state,
      configSettingsApi.endpoints.getConfigurationSettings.select({
        api_set: true,
      }),
      configSettingsApi.endpoints.getConfigurationSettings.select({
        api_set: false,
      }),
    ],
    (_, { data: apiSetConfig }, { data: configSetConfig }) => {
      // Return a single state contains the current CORS config with both
      // config-set and api-set values
      const currentCORSOriginSettings: CORSOriginsSettings = {
        configSet: {
          cors_origins: configSetConfig?.security?.cors_origins || [],
          cors_origin_regex: configSetConfig?.security?.cors_origin_regex,
        },
        apiSet: {
          cors_origins: apiSetConfig?.security?.cors_origins || [],
        },
      };
      return currentCORSOriginSettings;
    },
  );

export const selectApplicationConfig = () =>
  createSelector(
    [
      (state) => state,
      configSettingsApi.endpoints.getConfigurationSettings.select({
        api_set: true,
      }),
    ],
    (_, { data }) => data as ApplicationConfig,
  );

const defaultGppSettings: PrivacyExperienceGPPSettings = {
  enabled: false,
  cmp_api_required: false,
};

/**
 * Helper function to select a setting from the API or config set.
 * The API set value takes precedence over the config set value.
 * If neither the API set nor the config set has a value, then
 * the default value is returned.
 */
const selectSetting = (
  settingField: string,
  defaultSetting: any,
  apiSetConfig?: Record<string, any>,
  config?: Record<string, any>,
) => {
  const hasApi = apiSetConfig && apiSetConfig[settingField];
  const hasDefault = config && config[settingField];
  if (hasApi && hasDefault) {
    return { ...config[settingField], ...apiSetConfig[settingField] };
  }

  if (hasDefault) {
    return config[settingField];
  }

  if (hasApi) {
    return { ...apiSetConfig[settingField] };
  }

  return defaultSetting;
};

export const selectGppSettings: (
  state: RootState,
) => PrivacyExperienceGPPSettings = createSelector(
  [
    (state) => state,
    configSettingsApi.endpoints.getConfigurationSettings.select({
      api_set: true,
    }),
    configSettingsApi.endpoints.getConfigurationSettings.select({
      api_set: false,
    }),
  ],
  (state, { data: apiSetConfig }, { data: config }) => {
    return selectSetting("gpp", defaultGppSettings, apiSetConfig, config);
  },
);

const defaultPlusConsentSettings: PlusConsentSettingsApplicationConfig = {
  tcf_publisher_country_code: null,
};

export const selectPlusConsentSettings: (
  state: RootState,
) => PlusConsentSettingsApplicationConfig = createSelector(
  [
    (state) => state,
    configSettingsApi.endpoints.getConfigurationSettings.select({
      api_set: true,
    }),
    configSettingsApi.endpoints.getConfigurationSettings.select({
      api_set: false,
    }),
  ],
  (state, { data: apiSetConfig }, { data: config }) => {
    return selectSetting(
      "plus_consent_settings",
      defaultPlusConsentSettings,
      apiSetConfig,
      config,
    );
  },
);
