import { createSelector, createSlice } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import { TaxonomyEntity as SystemGroup } from "~/features/taxonomy/types";

const systemGroupApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllSystemGroups: build.query<SystemGroup[], void>({
      query: () => ({ url: `system_group` }),
      providesTags: () => ["System Groups"],
      transformResponse: (systemGroups: SystemGroup[]) =>
        systemGroups.sort((a, b) => a.fides_key.localeCompare(b.fides_key)),
    }),
    updateSystemGroup: build.mutation<
      SystemGroup,
      Partial<SystemGroup> & Pick<SystemGroup, "fides_key">
    >({
      query: (systemGroup) => ({
        url: `system_group`,
        params: { resource_type: "system_group" },
        method: "PUT",
        body: systemGroup,
      }),
      invalidatesTags: ["System Groups"],
    }),
    createSystemGroup: build.mutation<SystemGroup, Partial<SystemGroup>>({
      query: (systemGroup) => ({
        url: `system_group`,
        method: "POST",
        body: systemGroup,
      }),
      invalidatesTags: ["System Groups"],
    }),
    deleteSystemGroup: build.mutation<string, string>({
      query: (key) => ({
        url: `system_group/${key}`,
        params: { resource_type: "system_group" },
        method: "DELETE",
      }),
      invalidatesTags: ["System Groups"],
    }),
  }),
});

export const {
  useGetAllSystemGroupsQuery,
  useLazyGetAllSystemGroupsQuery,
  useUpdateSystemGroupMutation,
  useCreateSystemGroupMutation,
  useDeleteSystemGroupMutation,
} = systemGroupApi;

export interface State {}
const initialState: State = {};

export const systemGroupSlice = createSlice({
  name: "systemGroup",
  initialState,
  reducers: {},
});

const emptySystemGroups: SystemGroup[] = [];
export const selectSystemGroups: (state: RootState) => SystemGroup[] =
  createSelector(
    [
      (_state: RootState) => _state,
      systemGroupApi.endpoints.getAllSystemGroups.select(),
    ],
    (_state, { data }) => data ?? emptySystemGroups,
  );

export const selectEnabledSystemGroups = createSelector(
  selectSystemGroups,
  (items) => items.filter((item) => item.active),
);

export const { reducer } = systemGroupSlice;
