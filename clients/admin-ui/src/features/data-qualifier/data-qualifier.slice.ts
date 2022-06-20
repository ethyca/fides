import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import type { AppState } from "~/app/store";
import { DataQualifier } from "./types";

export interface State {
  dataQualifier: DataQualifier;
}

const initialState: State = {
  dataQualifier: {
    fides_key: "",
    organization_fides_key: "default_organization",
    name: "",
    description: "",
    parent_key: null,
  },
};

export const dataQualifierApi = createApi({
  reducerPath: "dataQualifierApi",
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_FIDESCTL_API,
  }),
  tagTypes: ["Data Qualifier"],
  endpoints: (build) => ({
    getDataQualifier: build.query<DataQualifier, void>({
      query: () => ({ url: `data_qualifier/` }),
      providesTags: () => ["Data Qualifier"],
    }),
  }),
});

export const { useGetDataQualifierQuery } = dataQualifierApi;

export const dataQualifierSlice = createSlice({
  name: "dataQualifier",
  initialState,
  reducers: {
    setDataQualifier: (state, action: PayloadAction<DataQualifier>) => ({
      ...state,
      dataQualifier: action.payload,
    }),
  },
});

export const { setDataQualifier } = dataQualifierSlice.actions;
export const selectDataQualifier = (state: AppState) =>
  state.dataQualifier.dataQualifier;

export const { reducer } = dataQualifierSlice;
