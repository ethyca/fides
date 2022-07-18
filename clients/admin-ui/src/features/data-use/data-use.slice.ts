import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import type { AppState } from "~/app/store";

import { DataUse } from "./types";

export interface State {
  dataUses: DataUse[];
}

const initialState: State = {
  dataUses: [],
};

export const dataUseApi = createApi({
  reducerPath: "dataUseApi",
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_FIDESCTL_API,
  }),
  tagTypes: ["Data Uses"],
  endpoints: (build) => ({
    getAllDataUses: build.query<DataUse[], void>({
      query: () => ({ url: `data_use/` }),
      providesTags: () => ["Data Uses"],
    }),
  }),
});

export const { useGetAllDataUsesQuery } = dataUseApi;

export const dataUseSlice = createSlice({
  name: "dataUse",
  initialState,
  reducers: {
    setDataUses: (state, action: PayloadAction<any>) => ({
      ...state,
      dataUses: action.payload,
    }),
  },
});

export const { setDataUses } = dataUseSlice.actions;
export const selectDataUses = (state: AppState) => state.dataUse.dataUses;

export const { reducer } = dataUseSlice;
