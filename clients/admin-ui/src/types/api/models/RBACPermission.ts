/**
 * RBAC Permission model for dynamic role-based access control.
 */
export interface RBACPermission {
  id: string;
  code: string;
  description?: string | null;
  resource_type?: string | null;
  is_active: boolean;
}
