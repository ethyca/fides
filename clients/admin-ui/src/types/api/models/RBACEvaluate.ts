/**
 * RBAC Permission evaluation request and response models.
 */
export interface RBACEvaluateRequest {
  user_id: string;
  permission_code: string;
  resource_type?: string | null;
  resource_id?: string | null;
}

export interface RBACEvaluateResponse {
  has_permission: boolean;
  reason: string;
  evaluated_roles: string[];
  matched_via?: "direct" | "inherited" | null;
}
