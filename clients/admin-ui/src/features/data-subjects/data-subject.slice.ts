import { createSelector, createSlice } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import { DataSubject_Input } from "~/types/api";

const dataSubjectsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllDataSubjects: build.query<DataSubject_Input[], void>({
      query: () => ({ url: `data_subject` }),
      providesTags: () => ["Data Subjects"],
      transformResponse: (subjects: DataSubject_Input[]) =>
        subjects.sort((a, b) => a.fides_key.localeCompare(b.fides_key)),
    }),
    updateDataSubject: build.mutation<
      DataSubject_Input,
      Partial<DataSubject_Input> & Pick<DataSubject_Input, "fides_key">
    >({
      query: (dataSubject) => ({
        url: `data_subject`,
        params: { resource_type: "data_subject" },
        method: "PUT",
        body: dataSubject,
      }),
      invalidatesTags: ["Data Subjects"],
    }),
    createDataSubject: build.mutation<DataSubject_Input, DataSubject_Input>({
      query: (dataSubject) => ({
        url: `data_subject`,
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

const emptyDataSubjects: DataSubject_Input[] = [];
export const selectDataSubjects: (state: RootState) => DataSubject_Input[] =
  createSelector(
    [
      (RootState) => RootState,
      dataSubjectsApi.endpoints.getAllDataSubjects.select(),
    ],
    (RootState, { data }) => data ?? emptyDataSubjects
  );

export const selectEnabledDataSubjects = createSelector(
  selectDataSubjects,
  (dataSubjects) => dataSubjects.filter((ds) => ds.active) ?? emptyDataSubjects
);

export const selectDataSubjectsMap = createSelector(
  selectDataSubjects,
  (dataSubjects) =>
    new Map(dataSubjects.map((dataSubject) => [dataSubject.name, dataSubject]))
);

export const { reducer } = dataSubjectsSlice;
