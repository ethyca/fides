import { RestrictionType, VendorRestriction } from "./constants";

export interface PurposeRestriction {
  restriction_type: RestrictionType;
  vendor_restriction: VendorRestriction;
  vendor_ids: string[];
  purpose_id?: number;
}

export interface FormValues {
  restriction_type: RestrictionType | "";
  vendor_restriction: VendorRestriction | "";
  vendor_ids?: string[];
}

export interface VendorRange {
  start: number;
  end: number | null;
}
