import { createSelector, createSlice } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import {
  LocationRegulationResponse,
  LocationRegulationSelections,
} from "~/types/api";

const locationsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getLocationsRegulations: build.query<LocationRegulationResponse, void>({
      query: () => ({
        url: `/plus/locations`,
      }),
      providesTags: () => ["Locations"],
    }),
    patchLocationsRegulations: build.mutation<
      LocationRegulationResponse,
      LocationRegulationSelections
    >({
      query: (body) => ({
        method: "PATCH",
        url: `plus/locations`,
        body,
      }),
      invalidatesTags: () => ["Locations"],
    }),
  }),
});

export const {
  useGetLocationsRegulationsQuery,
  usePatchLocationsRegulationsMutation,
} = locationsApi;

export const locationsSlice = createSlice({
  name: "locations",
  initialState: {},
  reducers: {},
});

export const { reducer } = locationsSlice;

const emptyLocationRegulation: LocationRegulationResponse = {
  locations: [],
  regulations: [],
};
export const selectLocationsRegulations: (
  state: RootState,
) => LocationRegulationResponse = createSelector(
  [
    (RootState) => RootState,
    locationsApi.endpoints.getLocationsRegulations.select(),
  ],
  (RootState, { data }) => data ?? emptyLocationRegulation,
);
