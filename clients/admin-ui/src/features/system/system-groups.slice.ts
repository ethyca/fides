import { createSelector, createSlice } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import { TaxonomyEntity } from "~/features/taxonomy/types";
import { SystemGroup } from "~/types/api/models/SystemGroup";
import { SystemGroupCreate } from "~/types/api/models/SystemGroupCreate";
import { SystemGroupUpdate } from "~/types/api/models/SystemGroupUpdate";

const systemGroupsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllSystemGroups: build.query<SystemGroup[], void>({
      query: () => ({ url: `system-groups` }),
      providesTags: () => ["System Groups"],
      transformResponse: (systemGroups: SystemGroup[]) =>
        systemGroups.sort((a, b) => a.fides_key.localeCompare(b.fides_key)),
    }),
    updateSystemGroup: build.mutation<
      SystemGroup,
      SystemGroupUpdate & { fides_key: string }
    >({
      query: (group) => ({
        url: `system-groups/${group.fides_key}`,
        method: "PUT",
        body: group,
      }),
      invalidatesTags: ["System Groups", "System"],
    }),
    createSystemGroup: build.mutation<SystemGroup, SystemGroupCreate>({
      query: (group) => ({
        url: `system-groups`,
        method: "POST",
        body: group,
      }),
      invalidatesTags: ["System Groups", "System"],
    }),
    deleteSystemGroup: build.mutation<{ fides_key: string }, string>({
      query: (fides_key) => ({
        url: `system-groups/${fides_key}`,
        method: "DELETE",
      }),
      invalidatesTags: ["System Groups", "System"],
    }),
  }),
});

export const {
  useGetAllSystemGroupsQuery,
  useLazyGetAllSystemGroupsQuery,
  useUpdateSystemGroupMutation,
  useCreateSystemGroupMutation,
  useDeleteSystemGroupMutation,
} = systemGroupsApi;

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
    systemGroupsApi.endpoints.getAllSystemGroups.select(),
    ({ data }) => data ?? emptySystemGroups,
  );

export const selectEnabledSystemGroups = createSelector(
  selectSystemGroups,
  (items) => items.filter((item) => item.active),
);

// Compatibility selector for taxonomy hooks that expect TaxonomyEntity[]
const emptyTaxonomyEntities: TaxonomyEntity[] = [];
export const selectSystemGroupsAsTaxonomyEntities: (
  state: RootState,
) => TaxonomyEntity[] = createSelector(
  systemGroupsApi.endpoints.getAllSystemGroups.select(),
  ({ data }) => data ?? emptyTaxonomyEntities,
);

export const { reducer } = systemGroupSlice;
