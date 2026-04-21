export interface IDPAuthorizeResponse {
  authorization_url: string;
  state: string;
}

export interface IDPCallbackResponse {
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  verification_token: string;
}

export interface IDPVerifiedRequestPayload {
  verification_token: string;
  policy_key: string;
  property_id?: string;
  custom_privacy_request_fields?: Record<string, unknown>;
}
