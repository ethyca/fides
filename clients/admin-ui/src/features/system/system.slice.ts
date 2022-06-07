import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { HYDRATE } from "next-redux-wrapper";

import { System } from "./types";

export interface State {
  systems: System[];
}

const initialState: State = {
  systems: [],
};

export const systemApi = createApi({
  reducerPath: "systemApi",
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_FIDESCTL_API,
  }),
  tagTypes: ["System"],
  endpoints: (build) => ({
    getAllSystems: build.query<System[], void>({
      query: () => ({ url: `system/` }),
      providesTags: () => ["System"],
    }),
  }),
});

export const { useGetAllSystemsQuery } = systemApi;

export const systemSlice = createSlice({
  name: "system",
  initialState,
  reducers: {
    setSystems: (state, action: PayloadAction<System[]>) => ({
      systems: action.payload,
    }),
  },
  extraReducers: {
    [HYDRATE]: (state, action) => ({
      ...state,
      ...action.payload.datasets,
    }),
  },
});

export const { setSystems } = systemSlice.actions;

export const { reducer } = systemSlice;
