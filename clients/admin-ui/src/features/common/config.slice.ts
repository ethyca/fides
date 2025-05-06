import { createSlice } from "@reduxjs/toolkit";

import { baseApi } from "~/features/common/api.slice";
import { ApplicationConfig } from "~/types/api";

export const configApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getConfig: build.query<ApplicationConfig, void>({
      query: () => ({
        method: "GET",
        url: "config",
      }),
      providesTags: () => ["Configuration Settings"],
    }),
  }),
});

export const { useGetConfigQuery } = configApi;

export interface State {
  applicationConfig?: ApplicationConfig;
}

const initialState: State = {};

export const applicationConfigSlice = createSlice({
  name: "applicationConfig",
  initialState,
  reducers: {},
});

export const { reducer } = applicationConfigSlice;
