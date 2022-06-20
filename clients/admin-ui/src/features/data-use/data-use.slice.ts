import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import type { AppState } from "~/app/store";

import { DataUse } from "./types";

export interface State {
  dataUse: DataUse[];
}

const initialState: State = {
  dataUse: [],
};

export const dataUseApi = createApi({
  reducerPath: "dataUseApi",
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_FIDESCTL_API,
  }),
  tagTypes: ["Data Use"],
  endpoints: (build) => ({
    getDataUse: build.query<DataUse, void>({
      query: () => ({ url: `data_use/` }),
      providesTags: () => ["Data Use"],
    }),
  }),
});

export const { useGetDataUseQuery } = dataUseApi;

export const dataUseSlice = createSlice({
  name: "dataUse",
  initialState,
  reducers: {
    setDataUse: (state, action: PayloadAction<DataUse>) => ({
      ...state,
      dataUse: action.payload,
    }),
  },
});

export const { setDataUse } = dataUseSlice.actions;
export const selectDataUse = (state: AppState) => state.dataUse.dataUse;

export const { reducer } = dataUseSlice;
