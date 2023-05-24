import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { VerificationType } from "~/components/modals/types";
import { baseApi } from "~/features/common/api.slice";
import {
  ComponentType,
  ConsentPreferences,
  ConsentPreferencesWithVerificationCode,
  Page_PrivacyExperienceResponse_,
  PrivacyNoticeRegion,
  PrivacyPreferencesRequest,
} from "~/types/api";

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
          ...payload,
        },
      }),
      providesTags: ["Privacy Experience"],
    }),
    updatePrivacyPreferencesVerified: build.mutation<
      void,
      { id: string; body: PrivacyPreferencesRequest }
    >({
      query: ({ id, body }) => ({
        url: `${VerificationType.ConsentRequest}/${id}/privacy-preferences`,
        method: "PATCH",
        body,
      }),
      invalidatesTags: ["Privacy Experience"],
    }),
    updatePrivacyPreferencesUnverified: build.mutation<
      void,
      PrivacyPreferencesRequest
    >({
      query: (payload) => ({
        url: `privacy-preferences`,
        method: "PATCH",
        body: payload,
      }),
      invalidatesTags: ["Privacy Experience"],
    }),
  }),
});

export const {
  usePostConsentRequestVerificationMutation,
  useLazyGetConsentRequestPreferencesQuery,
  useUpdateConsentRequestPreferencesDeprecatedMutation,
  useGetPrivacyExperienceQuery,
  useUpdatePrivacyPreferencesUnverifiedMutation,
  useUpdatePrivacyPreferencesVerifiedMutation,
} = consentApi;

type State = {
  /** The consent choices currently shown in the UI */
  fidesKeyToConsent: FidesKeyToConsent;
  /** The consent choices stored on the server (returned by the most recent API call). */
  persistedFidesKeyToConsent: FidesKeyToConsent;
  /** The region the user is in */
  region: PrivacyNoticeRegion | undefined;
  /** User id based on the device */
  fidesUserDeviceId: string | undefined;
};

const initialState: State = {
  fidesKeyToConsent: {},
  persistedFidesKeyToConsent: {},
  region: undefined,
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

    setRegion(draftState, { payload }: PayloadAction<PrivacyNoticeRegion>) {
      draftState.region = payload;
    },
    setFidesUserDeviceId(draftState, { payload }: PayloadAction<string>) {
      draftState.fidesUserDeviceId = payload;
    },
  },
});

export const { reducer } = consentSlice;
export const {
  changeConsent,
  updateUserConsentPreferencesFromApi,
  setRegion,
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
export const selectExperienceRegion = createSelector(
  selectConsentState,
  (state) => state.region
);
export const selectfidesUserDeviceId = createSelector(
  selectConsentState,
  (state) => state.fidesUserDeviceId
);
export const selectPrivacyExperience = createSelector(
  [(RootState) => RootState, selectExperienceRegion, selectfidesUserDeviceId],
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
