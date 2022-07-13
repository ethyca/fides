import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import type { AppState } from "~/app/store";
import { DataSubject } from "~/types/api";

export interface State {
  dataSubjects: DataSubject[];
}

const initialState: State = {
  dataSubjects: [],
};

export const dataSubjectsApi = createApi({
  reducerPath: "dataSubjectsApi",
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_FIDESCTL_API,
  }),
  tagTypes: ["Data Subject"],
  endpoints: (build) => ({
    getAllDataSubjects: build.query<DataSubject[], void>({
      query: () => ({ url: `data_subject/` }),
      providesTags: () => ["Data Subject"],
    }),
  }),
});

export const { useGetAllDataSubjectsQuery } = dataSubjectsApi;

export const dataSubjectsSlice = createSlice({
  name: "dataSubjects",
  initialState,
  reducers: {
    setDataSubjects: (state, action: PayloadAction<DataSubject[]>) => ({
      ...state,
      dataSubjects: action.payload,
    }),
  },
});

export const { setDataSubjects } = dataSubjectsSlice.actions;
export const selectDataSubjects = (state: AppState) =>
  state.dataSubjects.dataSubjects;

export const { reducer } = dataSubjectsSlice;
