import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

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
} from "~/types/api";
import { transformUserPreferenceToBoolean } from "./helpers";

import { FidesKeyToConsent } from "./types";

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
      PrivacyNoticeRegion
    >({
      query: (region) => ({
        url: "privacy-experience/",
        params: {
          component: ComponentType.PRIVACY_CENTER,
          region, // TODO: get from geolocation API?
          has_notices: true,
          show_disabled: false,
        },
      }),
      providesTags: ["Privacy Experience"],
    }),
    updatePrivacyPreferencesVerified: build.mutation<
      void,
      { id: string; body: CurrentPrivacyPreferenceSchema }
    >({
      query: ({ id, body }) => ({
        url: `${VerificationType.ConsentRequest}/${id}/privacy-preferences`,
        method: "PATCH",
        body,
      }),
      invalidatesTags: ["Privacy Preferences"],
    }),
    updatePrivacyPreferencesUnverified: build.mutation<
      void,
      CurrentPrivacyPreferenceSchema
    >({
      query: (payload) => ({
        url: `privacy-preferences`,
        method: "PATCH",
        body: payload,
      }),
      invalidatesTags: ["Privacy Preferences"],
    }),
  }),
});

export const {
  usePostConsentRequestVerificationMutation,
  useLazyGetConsentRequestPreferencesQuery,
  useUpdateConsentRequestPreferencesDeprecatedMutation,
  useGetPrivacyExperienceQuery,
} = consentApi;

type State = {
  /** The consent choices currently shown in the UI */
  fidesKeyToConsent: FidesKeyToConsent;
  /** The consent choices stored on the server (returned by the most recent API call). */
  persistedFidesKeyToConsent: FidesKeyToConsent;
  /** The region the user is in */
  region: PrivacyNoticeRegion | undefined;
};

const initialState: State = {
  fidesKeyToConsent: {},
  persistedFidesKeyToConsent: {},
  region: undefined,
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
  },
});

export const { reducer } = consentSlice;
export const { changeConsent, updateUserConsentPreferencesFromApi, setRegion } =
  consentSlice.actions;

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
export const selectPrivacyExperience = createSelector(
  [(RootState) => RootState, selectExperienceRegion],
  (RootState, region) => {
    if (!region) {
      return undefined;
    }
    return consentApi.endpoints.getPrivacyExperience.select(region)(RootState)
      ?.data?.items[0];
  }
);

const emptyConsentPreferences: FidesKeyToConsent = {};
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
    const preferences: FidesKeyToConsent = {};
    experience.privacy_notices.forEach((notice) => {
      // TODO: use notice.notice_key
      preferences[notice.id] = notice.current_preference
        ? transformUserPreferenceToBoolean(notice.current_preference)
        : undefined;
    });
    return preferences;
  }
);
