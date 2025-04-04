export const FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS = [1, 3, 4, 5, 6];
export const PUBLISHER_RESTRICTIONS_DOCS_URL =
  "https://ethyca.com/docs/tutorials/consent-management/consent-management-configuration/configure-tcf#vendor-overrides";

export enum RestrictionType {
  PURPOSE_RESTRICTION = "purpose_restriction",
  REQUIRE_CONSENT = "require_consent",
  REQUIRE_LEGITIMATE_INTEREST = "require_legitimate_interest",
}

export enum VendorRestriction {
  RESTRICT_ALL = "restrict_all",
  RESTRICT_SPECIFIC = "restrict_specific",
  ALLOW_SPECIFIC = "allow_specific",
}

export const RESTRICTION_TYPE_LABELS: Record<RestrictionType, string> = {
  [RestrictionType.PURPOSE_RESTRICTION]: "Purpose restriction",
  [RestrictionType.REQUIRE_CONSENT]: "Require consent",
  [RestrictionType.REQUIRE_LEGITIMATE_INTEREST]: "Require legitimate interest",
};

export const VENDOR_RESTRICTION_LABELS: Record<VendorRestriction, string> = {
  [VendorRestriction.RESTRICT_ALL]: "Restrict all vendors",
  [VendorRestriction.RESTRICT_SPECIFIC]: "Restrict specific vendors",
  [VendorRestriction.ALLOW_SPECIFIC]: "Allow specific vendors",
};
