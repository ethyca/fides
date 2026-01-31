/**
 * RBAC Role model for dynamic role-based access control.
 */
export interface RBACRole {
  id: string;
  name: string;
  key: string;
  description?: string | null;
  parent_role_id?: string | null;
  priority: number;
  is_system_role: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  permissions: string[];
  inherited_permissions: string[];
}

export interface RBACRoleCreate {
  name: string;
  key: string;
  description?: string | null;
  parent_role_id?: string | null;
  priority?: number;
}

export interface RBACRoleUpdate {
  name?: string;
  description?: string | null;
  parent_role_id?: string | null;
  priority?: number;
  is_active?: boolean;
}

export interface RBACRolePermissionsUpdate {
  permission_codes: string[];
}
