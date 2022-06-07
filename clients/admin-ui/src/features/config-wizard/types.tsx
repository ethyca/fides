export interface Organization {
  description: string;
  fides_key: string;
  name: string;
}

export interface OrganizationParams {
  page: number;
  size: number;
}

export interface OrganizationResponse {
  response: {};
}

export interface OrganizationUpdate {
  response: {};
}
