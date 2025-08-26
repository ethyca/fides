import { LocationRegulationResponse } from "~/types/api";
import { baseApi } from "./api.slice";

export const locationApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getLocations: build.query<LocationRegulationResponse, {}>({
      query: (params) => ({
        url: `plus/locations`,
        params,
      }),
    }),
  }),
});

export const { useGetLocationsQuery } = locationApi;
