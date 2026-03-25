/**
 * RBAC User Role assignment model for dynamic role-based access control.
 */
export interface RBACUserRole {
  id: string;
  user_id: string;
  role_id: string;
  role_key: string;
  role_name: string;
  resource_type?: string | null;
  resource_id?: string | null;
  valid_from?: string | null;
  valid_until?: string | null;
  is_valid: boolean;
  assigned_by?: string | null;
  created_at: string;
}

export interface RBACUserRoleCreate {
  role_id: string;
  resource_type?: string | null;
  resource_id?: string | null;
  valid_from?: string | null;
  valid_until?: string | null;
}
