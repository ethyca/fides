import { baseApi } from "~/features/common/api.slice";

export interface ControlGroup {
  key: string;
  label: string;
}

export interface AccessPolicy {
  id: string;
  name: string;
  description?: string;
  control_group?: string;
  yaml?: string;
  created_at?: string;
  updated_at?: string;
}

export interface AccessPolicyListResponse {
  items: AccessPolicy[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

const accessPoliciesApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAccessPolicies: build.query<
      AccessPolicyListResponse,
      { page?: number; size?: number }
    >({
      query: ({ page = 1, size = 50 } = {}) => ({
        method: "GET",
        url: "plus/access-policy",
        params: { page, size },
      }),
      providesTags: () => ["Access Policies"],
    }),
    getAccessPolicy: build.query<AccessPolicy, string>({
      query: (id) => ({
        method: "GET",
        url: `plus/access-policy/${id}`,
      }),
      providesTags: (_result, _error, id) => [{ type: "Access Policies", id }],
    }),
    createAccessPolicy: build.mutation<AccessPolicy, Partial<AccessPolicy>>({
      query: (body) => ({
        method: "POST",
        url: "plus/access-policy",
        body,
      }),
      invalidatesTags: ["Access Policies"],
    }),
    updateAccessPolicy: build.mutation<
      AccessPolicy,
      { id: string } & Partial<AccessPolicy>
    >({
      query: ({ id, ...body }) => ({
        method: "PUT",
        url: `plus/access-policy/${id}`,
        body,
      }),
      invalidatesTags: (_result, _error, { id }) => [
        "Access Policies",
        { type: "Access Policies", id },
      ],
    }),
    deleteAccessPolicy: build.mutation<void, string>({
      query: (id) => ({
        method: "DELETE",
        url: `plus/access-policy/${id}`,
      }),
      invalidatesTags: ["Access Policies"],
    }),
    getControlGroups: build.query<ControlGroup[], void>({
      query: () => ({
        method: "GET",
        url: "plus/access-policy/control-group",
      }),
      providesTags: ["Access Policy Control Groups"],
    }),
  }),
});

export const {
  useGetAccessPoliciesQuery,
  useGetAccessPolicyQuery,
  useCreateAccessPolicyMutation,
  useUpdateAccessPolicyMutation,
  useDeleteAccessPolicyMutation,
  useGetControlGroupsQuery,
} = accessPoliciesApi;
