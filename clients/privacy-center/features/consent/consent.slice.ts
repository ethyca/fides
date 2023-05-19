import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { VerificationType } from "~/components/modals/types";
import { baseApi } from "~/features/common/api.slice";
import {
  ComponentType,
  ConsentPreferences,
  ConsentPreferencesWithVerificationCode,
  PrivacyExperienceResponse,
  PrivacyNoticeRegion,
} from "~/types/api";

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
    updateConsentRequestPreferences: build.mutation<
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
      PrivacyExperienceResponse,
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
  }),
});

export const {
  usePostConsentRequestVerificationMutation,
  useLazyGetConsentRequestPreferencesQuery,
  useUpdateConsentRequestPreferencesMutation,
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
      ?.data;
  }
);
