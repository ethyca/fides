import { LocationRegulationResponse } from "~/types/api";

import { baseApi } from "./api.slice";

export const locationApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getLocations: build.query<LocationRegulationResponse, void>({
      query: () => ({
        url: `plus/locations`,
      }),
    }),
  }),
});

export const { useGetLocationsQuery } = locationApi;
