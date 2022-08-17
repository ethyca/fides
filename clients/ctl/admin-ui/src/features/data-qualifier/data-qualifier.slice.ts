import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import type { AppState } from "~/app/store";
import { DataQualifier } from "~/types/api";

export interface State {
  dataQualifier: DataQualifier[];
}

const initialState: State = {
  dataQualifier: [],
};

export const dataQualifierApi = createApi({
  reducerPath: "dataQualifierApi",
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_FIDESCTL_API,
  }),
  tagTypes: ["Data Qualifiers"],
  endpoints: (build) => ({
    getAllDataQualifiers: build.query<DataQualifier[], void>({
      query: () => ({ url: `data_qualifier/` }),
      providesTags: () => ["Data Qualifiers"],
      transformResponse: (qualifiers: DataQualifier[]) =>
        qualifiers.sort((a, b) => a.fides_key.localeCompare(b.fides_key)),
    }),

    updateDataQualifier: build.mutation<
      DataQualifier,
      Partial<DataQualifier> & Pick<DataQualifier, "fides_key">
    >({
      query: (dataQualifier) => ({
        url: `data_qualifier/`,
        params: { resource_type: "data_qualifier" },
        method: "PUT",
        body: dataQualifier,
      }),
      invalidatesTags: ["Data Qualifiers"],
    }),
  }),
});

export const { useGetAllDataQualifiersQuery, useUpdateDataQualifierMutation } =
  dataQualifierApi;

export const dataQualifierSlice = createSlice({
  name: "dataQualifier",
  initialState,
  reducers: {
    setDataQualifiers: (state, action: PayloadAction<any>) => ({
      ...state,
      dataQualifier: action.payload,
    }),
  },
});

export const { setDataQualifiers } = dataQualifierSlice.actions;
export const selectDataQualifiers = (state: AppState) =>
  state.dataQualifier.dataQualifier;

export const { reducer } = dataQualifierSlice;
