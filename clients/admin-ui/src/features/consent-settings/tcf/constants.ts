import { TCFRestrictionType, TCFVendorRestriction } from "~/types/api";

export const FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS = [1, 3, 4, 5, 6];
export const PUBLISHER_RESTRICTIONS_DOCS_URL =
  "https://ethyca.com/docs/tutorials/consent-management/consent-management-configuration/configure-tcf#vendor-overrides";

export const RESTRICTION_TYPE_LABELS: Record<TCFRestrictionType, string> = {
  [TCFRestrictionType.PURPOSE_RESTRICTION]: "Purpose restriction",
  [TCFRestrictionType.REQUIRE_CONSENT]: "Require consent",
  [TCFRestrictionType.REQUIRE_LEGITIMATE_INTEREST]:
    "Require legitimate interest",
};

export const VENDOR_RESTRICTION_LABELS: Record<TCFVendorRestriction, string> = {
  [TCFVendorRestriction.RESTRICT_ALL_VENDORS]: "Restrict all vendors",
  [TCFVendorRestriction.RESTRICT_SPECIFIC_VENDORS]: "Restrict specific vendors",
  [TCFVendorRestriction.ALLOW_SPECIFIC_VENDORS]: "Allow specific vendors",
};
