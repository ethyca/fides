import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import type { RootState } from "~/app/store";
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
  tagTypes: ["Data Subjects"],
  endpoints: (build) => ({
    getAllDataSubjects: build.query<DataSubject[], void>({
      query: () => ({ url: `data_subject/` }),
      providesTags: () => ["Data Subjects"],
      transformResponse: (subjects: DataSubject[]) =>
        subjects.sort((a, b) => a.fides_key.localeCompare(b.fides_key)),
    }),
    updateDataSubject: build.mutation<
      DataSubject,
      Partial<DataSubject> & Pick<DataSubject, "fides_key">
    >({
      query: (dataSubject) => ({
        url: `data_subject/`,
        params: { resource_type: "data_subject" },
        method: "PUT",
        body: dataSubject,
      }),
      invalidatesTags: ["Data Subjects"],
    }),
    createDataSubject: build.mutation<DataSubject, DataSubject>({
      query: (dataSubject) => ({
        url: `data_subject/`,
        method: "POST",
        body: dataSubject,
      }),
      invalidatesTags: ["Data Subjects"],
    }),
    deleteDataSubject: build.mutation<string, string>({
      query: (key) => ({
        url: `data_subject/${key}`,
        params: { resource_type: "data_subject" },
        method: "DELETE",
      }),
      invalidatesTags: ["Data Subjects"],
    }),
  }),
});

export const {
  useGetAllDataSubjectsQuery,
  useUpdateDataSubjectMutation,
  useCreateDataSubjectMutation,
  useDeleteDataSubjectMutation,
} = dataSubjectsApi;

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
export const selectDataSubjects = (state: RootState) =>
  state.dataSubjects.dataSubjects;

export const { reducer } = dataSubjectsSlice;
