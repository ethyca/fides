export interface OktaAppMetadata {
  app_type?: string; // SAML_2_0, OPENID_CONNECT, BROWSER_PLUGIN, etc.
  status?: string; // ACTIVE, INACTIVE
  created?: string; // ISO timestamp
  sign_on_url?: string | null; // SSO login URL
  vendor_match_confidence?: "high" | "medium" | "low" | null;
  vendor_logo_url?: string | null;
}
