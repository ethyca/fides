/**
 * RBAC Constraint model for separation of duties and cardinality constraints.
 */
export enum RBACConstraintType {
  STATIC_SOD = "static_sod",
  DYNAMIC_SOD = "dynamic_sod",
  CARDINALITY = "cardinality",
}

export interface RBACConstraint {
  id: string;
  name: string;
  constraint_type: RBACConstraintType;
  role_id_1: string;
  role_id_2?: string | null;
  max_users?: number | null;
  description?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface RBACConstraintCreate {
  name: string;
  constraint_type: RBACConstraintType;
  role_id_1: string;
  role_id_2?: string | null;
  max_users?: number | null;
  description?: string | null;
}

export interface RBACConstraintUpdate {
  name?: string;
  max_users?: number | null;
  description?: string | null;
  is_active?: boolean;
}
