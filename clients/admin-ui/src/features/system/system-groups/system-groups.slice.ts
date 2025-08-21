import { baseApi } from "~/features/common/api.slice";
import { SystemGroup } from "~/types/api/models/SystemGroup";
import { SystemGroupCreate } from "~/types/api/models/SystemGroupCreate";
import { SystemGroupUpdate } from "~/types/api/models/SystemGroupUpdate";

const systemGroupsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllSystemGroups: build.query<SystemGroup[], void>({
      query: () => ({ url: `system-groups` }),
      providesTags: () => ["System Groups"],
    }),
    createSystemGroup: build.mutation<SystemGroupCreate, SystemGroup>({
      query: (group) => ({
        url: `system-groups`,
        method: "POST",
        body: group,
      }),
      invalidatesTags: ["System Groups", "System"],
    }),
    updateSystemGroup: build.mutation<SystemGroupUpdate, SystemGroup>({
      query: (group) => ({
        url: `system-groups/${group.fides_key}`,
        method: "PUT",
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
  useCreateSystemGroupMutation,
  useUpdateSystemGroupMutation,
  useDeleteSystemGroupMutation,
} = systemGroupsApi;

export interface State {}
