import { createSelector } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import { PurposesResponse } from "~/types/api";

export const purposeApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getPurposes: build.query<PurposesResponse, void>({
      query: () => "purposes",
    }),
  }),
});

export const { useGetPurposesQuery } = purposeApi;

const EMPTY_PURPOSES: PurposesResponse = {
  purposes: {},
  special_purposes: {},
};
export const selectPurposes: (state: RootState) => PurposesResponse =
  createSelector(
    purposeApi.endpoints.getPurposes.select(),
    ({ data }) => data || EMPTY_PURPOSES,
  );
