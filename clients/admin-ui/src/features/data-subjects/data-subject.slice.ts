import { createSelector, createSlice } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import type { RootState } from "~/app/store";
import { selectToken } from "~/features/auth";
import { addCommonHeaders } from "~/features/common/CommonHeaders";
import { DataSubject } from "~/types/api";

export const dataSubjectsApi = createApi({
  reducerPath: "dataSubjectsApi",
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_FIDESCTL_API,
    prepareHeaders: (headers, { getState }) => {
      const token: string | null = selectToken(getState() as RootState);
      addCommonHeaders(headers, token);
      return headers;
    },
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

export interface State {}
const initialState: State = {};

export const dataSubjectsSlice = createSlice({
  name: "dataSubjects",
  initialState,
  reducers: {},
});

const emptyDataSubjects: DataSubject[] = [];
export const selectDataSubjects: (state: RootState) => DataSubject[] =
  createSelector(
    dataSubjectsApi.endpoints.getAllDataSubjects.select(),
    ({ data }) => data ?? emptyDataSubjects
  );

export const selectDataSubjectsMap = createSelector(
  selectDataSubjects,
  (dataSubjects) =>
    new Map(dataSubjects.map((dataSubject) => [dataSubject.name, dataSubject]))
);

export const { reducer } = dataSubjectsSlice;
