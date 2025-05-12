import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";
import {
  constructFidesRegionString,
  RecordsServedResponse,
  UserGeolocation,
} from "fides-js";

import type { RootState } from "~/app/store";
import { VerificationType } from "~/components/modals/types";
import { baseApi } from "~/features/common/api.slice";
import {
  ComponentType,
  Consent,
  ConsentPreferences,
  ConsentPreferencesWithVerificationCode,
  PreferencesSaved,
  PrivacyExperienceResponse,
  PrivacyNoticeRegion,
  PrivacyPreferencesRequest,
  Property,
  RecordConsentServedRequest,
} from "~/types/api";

import { selectPropertyId } from "../common/property.slice";
import { selectSettings } from "../common/settings.slice";
import { FidesKeyToConsent } from "./types";

export interface PagePrivacyExperienceResponse {
  items: Array<PrivacyExperienceResponse>;
  total: number | null;
  page: number | null;
  size: number | null;
  pages?: number | null;
}

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
      PagePrivacyExperienceResponse,
      { region: PrivacyNoticeRegion; property_id: Property["id"] }
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
      PreferencesSaved,
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
    updateNoticesServed: build.mutation<
      RecordsServedResponse,
      { id: string; body: RecordConsentServedRequest }
    >({
      query: ({ id, body }) => ({
        url: `${VerificationType.ConsentRequest}/${id}/notices-served`,
        method: "PATCH",
        body,
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
  useUpdateNoticesServedMutation,
} = consentApi;

type State = {
  /** The consent choices currently shown in the UI */
  fidesKeyToConsent: FidesKeyToConsent;
  /** The consent choices stored on the server (returned by the most recent API call). */
  persistedFidesKeyToConsent: FidesKeyToConsent;
  /** User id based on the device */
  fidesUserDeviceId: string | undefined;
  /** Location (ex: US-CA) */
  location: string | undefined;
};

const initialState: State = {
  fidesKeyToConsent: {},
  persistedFidesKeyToConsent: {},
  fidesUserDeviceId: undefined,
  location: undefined,
};

export const consentSlice = createSlice({
  name: "consent",
  initialState,
  reducers: {
    changeConsent(
      draftState,
      {
        payload: { key, value },
      }: PayloadAction<{ key: string; value: boolean }>,
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
      { payload }: PayloadAction<ConsentPreferences>,
    ) {
      const consentPreferences = payload.consent ?? [];
      consentPreferences.forEach((consent: Consent) => {
        draftState.fidesKeyToConsent[consent.data_use] = consent.opt_in;
        draftState.persistedFidesKeyToConsent[consent.data_use] =
          consent.opt_in;
      });
    },

    setFidesUserDeviceId(
      draftState,
      { payload }: PayloadAction<string | undefined>,
    ) {
      draftState.fidesUserDeviceId = payload;
    },

    setLocation(draftState, action: PayloadAction<string | undefined>) {
      draftState.location = action.payload;
    },

    clearLocation(draftState) {
      draftState.location = undefined;
    },
  },
});

export const { reducer } = consentSlice;
export const {
  changeConsent,
  updateUserConsentPreferencesFromApi,
  setFidesUserDeviceId,
  setLocation,
  clearLocation,
} = consentSlice.actions;

export const selectConsentState = (state: RootState) => state.consent;

export const selectFidesKeyToConsent = createSelector(
  selectConsentState,
  (state) => state.fidesKeyToConsent,
);

export const selectPersistedFidesKeyToConsent = createSelector(
  selectConsentState,
  (state) => state.persistedFidesKeyToConsent,
);

// Privacy experience
export const selectFidesUserDeviceId = createSelector(
  selectConsentState,
  (state) => state.fidesUserDeviceId,
);

export const selectUserRegion = createSelector(
  [(RootState) => RootState, selectConsentState, selectSettings],
  (RootState, consentState, settingsState) => {
    const { settings } = settingsState;
    if (settings?.IS_GEOLOCATION_ENABLED && settings?.GEOLOCATION_API_URL) {
      let geolocation: UserGeolocation | undefined = {
        location: consentState.location,
      };

      if (!geolocation.location) {
        geolocation = consentApi.endpoints.getUserGeolocation.select(
          settings.GEOLOCATION_API_URL,
        )(RootState)?.data;
        return constructFidesRegionString(geolocation) as PrivacyNoticeRegion;
      }
      return geolocation.location as PrivacyNoticeRegion;
    }
    return undefined;
  },
);

export const selectPrivacyExperience = createSelector(
  [
    (RootState) => RootState,
    selectUserRegion,
    selectFidesUserDeviceId,
    selectPropertyId,
  ],
  (RootState, region, _deviceId, propertyId) => {
    if (!region) {
      return undefined;
    }
    return consentApi.endpoints.getPrivacyExperience.select({
      region,
      property_id: propertyId,
    })(RootState).data?.items[0];
  },
);
