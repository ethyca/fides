import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { constructFidesRegionString, UserGeolocation } from "fides-js";

import type { RootState } from "~/app/store";
import { VerificationType } from "~/components/modals/types";
import { baseApi } from "~/features/common/api.slice";
import {
  ComponentType,
  ConsentPreferences,
  ConsentPreferencesWithVerificationCode,
  CurrentPrivacyPreferenceSchema,
  Page_PrivacyExperienceResponse_,
  PrivacyNoticeRegion,
  PrivacyPreferencesRequest,
} from "~/types/api";
import { selectSettings } from "../common/settings.slice";

import { FidesKeyToConsent, NoticeHistoryIdToPreference } from "./types";

export const consentApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    postConsentRequestVerification: build.mutation<
      ConsentPreferences,
      {
        id: string;
        code: string;
      }
    >({
      query: ({ id, code }) => ({
        url: `${VerificationType.ConsentRequest}/${id}/verify`,
        method: "POST",
        body: {
          code,
        },
      }),
    }),
    getConsentRequestPreferences: build.query<
      ConsentPreferences,
      {
        id: string;
      }
    >({
      query: ({ id }) => `${VerificationType.ConsentRequest}/${id}/preferences`,
    }),
    /**
     * This endpoint is deprecated in favor of
     * /consent-request/{id}/privacy-preferences
     * */
    updateConsentRequestPreferencesDeprecated: build.mutation<
      ConsentPreferences,
      { id: string; body: ConsentPreferencesWithVerificationCode }
    >({
      query: ({ id, body }) => ({
        url: `${VerificationType.ConsentRequest}/${id}/preferences`,
        method: "PATCH",
        body,
        credentials: "include",
      }),
    }),
    getPrivacyExperience: build.query<
      Page_PrivacyExperienceResponse_,
      { region: PrivacyNoticeRegion; fides_user_device_id?: string }
    >({
      query: (payload) => ({
        url: "privacy-experience/",
        params: {
          component: ComponentType.PRIVACY_CENTER,
          has_notices: true,
          show_disabled: false,
          has_config: true,
          systems_applicable: true,
          ...payload,
        },
      }),
      providesTags: ["Privacy Experience"],
    }),
    updatePrivacyPreferences: build.mutation<
      CurrentPrivacyPreferenceSchema[],
      { id: string; body: PrivacyPreferencesRequest }
    >({
      query: ({ id, body }) => ({
        url: `${VerificationType.ConsentRequest}/${id}/privacy-preferences`,
        method: "PATCH",
        body,
      }),
      invalidatesTags: ["Privacy Experience"],
    }),
    getUserGeolocation: build.query<UserGeolocation, string>({
      query: (url) => ({
        url,
        method: "GET",
      }),
    }),
  }),
});

export const {
  usePostConsentRequestVerificationMutation,
  useLazyGetConsentRequestPreferencesQuery,
  useUpdateConsentRequestPreferencesDeprecatedMutation,
  useGetPrivacyExperienceQuery,
  useUpdatePrivacyPreferencesMutation,
  useGetUserGeolocationQuery,
} = consentApi;

type State = {
  /** The consent choices currently shown in the UI */
  fidesKeyToConsent: FidesKeyToConsent;
  /** The consent choices stored on the server (returned by the most recent API call). */
  persistedFidesKeyToConsent: FidesKeyToConsent;
  /** User id based on the device */
  fidesUserDeviceId: string | undefined;
};

const initialState: State = {
  fidesKeyToConsent: {},
  persistedFidesKeyToConsent: {},
  fidesUserDeviceId: undefined,
};

export const consentSlice = createSlice({
  name: "consent",
  initialState,
  reducers: {
    changeConsent(
      draftState,
      {
        payload: { key, value },
      }: PayloadAction<{ key: string; value: boolean }>
    ) {
      draftState.fidesKeyToConsent[key] = value;
    },

    /**
     * Update the stored consent preferences with the data returned by the API. These values take
     * precedence over the locally-stored opt in/out booleans to ensure the UI matches the server.
     *
     * Note: we have to store a copy of the API results instead of selecting from the API's cache
     * directly because there are 3 different endpoints that may return this info. If we simplify
     * how that fetching works with/without verification, this would also become simpler.
     */
    updateUserConsentPreferencesFromApi(
      draftState,
      { payload }: PayloadAction<ConsentPreferences>
    ) {
      const consentPreferences = payload.consent ?? [];
      consentPreferences.forEach((consent) => {
        draftState.fidesKeyToConsent[consent.data_use] = consent.opt_in;
        draftState.persistedFidesKeyToConsent[consent.data_use] =
          consent.opt_in;
      });
    },

    setFidesUserDeviceId(
      draftState,
      { payload }: PayloadAction<string | undefined>
    ) {
      draftState.fidesUserDeviceId = payload;
    },
  },
});

export const { reducer } = consentSlice;
export const {
  changeConsent,
  updateUserConsentPreferencesFromApi,
  setFidesUserDeviceId,
} = consentSlice.actions;

export const selectConsentState = (state: RootState) => state.consent;

export const selectFidesKeyToConsent = createSelector(
  selectConsentState,
  (state) => state.fidesKeyToConsent
);

export const selectPersistedFidesKeyToConsent = createSelector(
  selectConsentState,
  (state) => state.persistedFidesKeyToConsent
);

// Privacy experience
export const selectFidesUserDeviceId = createSelector(
  selectConsentState,
  (state) => state.fidesUserDeviceId
);

export const selectUserRegion = createSelector(
  [(RootState) => RootState, selectSettings],
  (RootState, settingsState) => {
    const { settings } = settingsState;
    if (settings?.IS_GEOLOCATION_ENABLED && settings?.GEOLOCATION_API_URL) {
      const geolocation = consentApi.endpoints.getUserGeolocation.select(
        settings.GEOLOCATION_API_URL
      )(RootState)?.data;
      return constructFidesRegionString(geolocation) as PrivacyNoticeRegion;
    }
    return undefined;
  }
);

export const selectPrivacyExperience = createSelector(
  [(RootState) => RootState, selectUserRegion, selectFidesUserDeviceId],
  (RootState, region, deviceId) => {
    if (!region) {
      return undefined;
    }
    return consentApi.endpoints.getPrivacyExperience.select({
      region,
      fides_user_device_id: deviceId,
    })(RootState)?.data?.items[0];
  }
);

const emptyConsentPreferences: NoticeHistoryIdToPreference = {};
export const selectCurrentConsentPreferences = createSelector(
  selectPrivacyExperience,
  (experience) => {
    if (
      !experience ||
      !experience.privacy_notices ||
      !experience.privacy_notices.length
    ) {
      return emptyConsentPreferences;
    }
    const preferences: NoticeHistoryIdToPreference = {};
    experience.privacy_notices.forEach((notice) => {
      preferences[notice.privacy_notice_history_id] = notice.current_preference;
    });
    return preferences;
  }
);
