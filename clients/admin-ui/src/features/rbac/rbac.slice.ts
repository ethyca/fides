import { baseApi } from "~/features/common/api.slice";
import {
  RBACConstraint,
  RBACConstraintCreate,
  RBACEvaluateRequest,
  RBACEvaluateResponse,
  RBACPermission,
  RBACRole,
  RBACRoleCreate,
  RBACRolePermissionsUpdate,
  RBACRoleUpdate,
  RBACUserRole,
  RBACUserRoleCreate,
} from "~/types/api";

const rbacApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    // Role endpoints
    getRoles: build.query<RBACRole[], { include_inactive?: boolean }>({
      query: (params) => ({
        url: `plus/rbac/roles`,
        params,
      }),
      providesTags: ["RBAC Roles"],
    }),

    getRoleById: build.query<RBACRole, string>({
      query: (roleId) => ({ url: `plus/rbac/roles/${roleId}` }),
      providesTags: (result, error, id) => [{ type: "RBAC Roles", id }],
    }),

    createRole: build.mutation<RBACRole, RBACRoleCreate>({
      query: (body) => ({
        url: `plus/rbac/roles`,
        method: "POST",
        body,
      }),
      invalidatesTags: ["RBAC Roles"],
    }),

    updateRole: build.mutation<RBACRole, { roleId: string; data: RBACRoleUpdate }>({
      query: ({ roleId, data }) => ({
        url: `plus/rbac/roles/${roleId}`,
        method: "PUT",
        body: data,
      }),
      invalidatesTags: (result, error, { roleId }) => [
        "RBAC Roles",
        { type: "RBAC Roles", id: roleId },
      ],
    }),

    deleteRole: build.mutation<void, string>({
      query: (roleId) => ({
        url: `plus/rbac/roles/${roleId}`,
        method: "DELETE",
      }),
      invalidatesTags: ["RBAC Roles"],
    }),

    updateRolePermissions: build.mutation<
      RBACRole,
      { roleId: string; data: RBACRolePermissionsUpdate }
    >({
      query: ({ roleId, data }) => ({
        url: `plus/rbac/roles/${roleId}/permissions`,
        method: "PUT",
        body: data,
      }),
      invalidatesTags: (result, error, { roleId }) => [
        "RBAC Roles",
        { type: "RBAC Roles", id: roleId },
      ],
    }),

    // Permission endpoints
    getPermissions: build.query<RBACPermission[], { resource_type?: string }>({
      query: (params) => ({
        url: `plus/rbac/permissions`,
        params,
      }),
      providesTags: ["RBAC Permissions"],
    }),

    // User role assignment endpoints
    getUserRoles: build.query<RBACUserRole[], { userId: string; include_expired?: boolean }>({
      query: ({ userId, ...params }) => ({
        url: `plus/rbac/users/${userId}/roles`,
        params,
      }),
      providesTags: (result, error, { userId }) => [
        { type: "RBAC User Roles", id: userId },
      ],
    }),

    assignUserRole: build.mutation<
      RBACUserRole,
      { userId: string; data: RBACUserRoleCreate }
    >({
      query: ({ userId, data }) => ({
        url: `plus/rbac/users/${userId}/roles`,
        method: "POST",
        body: data,
      }),
      invalidatesTags: (result, error, { userId }) => [
        { type: "RBAC User Roles", id: userId },
        "User",
      ],
    }),

    removeUserRole: build.mutation<void, { userId: string; assignmentId: string }>({
      query: ({ userId, assignmentId }) => ({
        url: `plus/rbac/users/${userId}/roles/${assignmentId}`,
        method: "DELETE",
      }),
      invalidatesTags: (result, error, { userId }) => [
        { type: "RBAC User Roles", id: userId },
        "User",
      ],
    }),

    // Constraint endpoints
    getConstraints: build.query<RBACConstraint[], void>({
      query: () => ({ url: `plus/rbac/constraints` }),
      providesTags: ["RBAC Constraints"],
    }),

    createConstraint: build.mutation<RBACConstraint, RBACConstraintCreate>({
      query: (body) => ({
        url: `plus/rbac/constraints`,
        method: "POST",
        body,
      }),
      invalidatesTags: ["RBAC Constraints"],
    }),

    deleteConstraint: build.mutation<void, string>({
      query: (constraintId) => ({
        url: `plus/rbac/constraints/${constraintId}`,
        method: "DELETE",
      }),
      invalidatesTags: ["RBAC Constraints"],
    }),

    // Permission evaluation
    evaluatePermission: build.mutation<RBACEvaluateResponse, RBACEvaluateRequest>({
      query: (body) => ({
        url: `plus/rbac/evaluate`,
        method: "POST",
        body,
      }),
    }),
  }),
});

export const {
  useGetRolesQuery,
  useGetRoleByIdQuery,
  useCreateRoleMutation,
  useUpdateRoleMutation,
  useDeleteRoleMutation,
  useUpdateRolePermissionsMutation,
  useGetPermissionsQuery,
  useGetUserRolesQuery,
  useAssignUserRoleMutation,
  useRemoveUserRoleMutation,
  useGetConstraintsQuery,
  useCreateConstraintMutation,
  useDeleteConstraintMutation,
  useEvaluatePermissionMutation,
} = rbacApi;
