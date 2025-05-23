import { TCFRestrictionType, TCFVendorRestriction } from "~/types/api";

export interface PurposeRestriction {
  id?: string;
  restriction_type: TCFRestrictionType;
  vendor_restriction: TCFVendorRestriction;
  vendor_ids: string[];
  purpose_id?: number;
}

export interface FormValues {
  restriction_type: TCFRestrictionType | "";
  vendor_restriction: TCFVendorRestriction | "";
  vendor_ids?: string[];
}

export interface VendorRange {
  start: number;
  end: number | null;
}
