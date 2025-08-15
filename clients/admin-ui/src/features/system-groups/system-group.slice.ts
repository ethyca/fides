import { createSelector, createSlice } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import { TaxonomyEntity as SystemGroup } from "~/features/taxonomy/types";

const systemGroupApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllSystemGroups: build.query<SystemGroup[], void>({
      query: () => ({ url: `system_group` }),
      providesTags: () => ["System Groups"],
      transformResponse: (items: SystemGroup[]) => {
        const result: SystemGroup[] = [];
        const remaining = [...items];

        // Add all root items first (no parent)
        const root = remaining.filter((i) => i.parent_key == null);
        root.sort((a, b) => a.fides_key.localeCompare(b.fides_key));
        result.push(...root);

        let pending = remaining.filter((i) => i.parent_key != null);
        while (pending.length) {
          const toAdd = pending.filter((i) =>
            result.some((r) => r.fides_key === i.parent_key),
          );
          if (toAdd.length === 0) {
            // break potential cycles – just append alphabetically
            result.push(
              ...pending.sort((a, b) => a.fides_key.localeCompare(b.fides_key)),
            );
            break;
          }
          toAdd.sort((a, b) => a.fides_key.localeCompare(b.fides_key));
          result.push(...toAdd);
          pending = pending.filter((i) => !toAdd.includes(i));
        }

        return result;
      },
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
