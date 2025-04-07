import { TCFRestrictionType, TCFVendorRestriction } from "~/types/api";

import {
  FormValues,
  PurposeRestriction,
} from "../../src/features/consent-settings/tcf/types";
import {
  checkForVendorRestrictionConflicts,
  doRangesOverlap,
  isValidVendorIdFormat,
  parseVendorIdToRange,
} from "../../src/features/consent-settings/tcf/validation-utils";

describe("isValidVendorIdFormat", () => {
  it("should return true for valid single numbers", () => {
    expect(isValidVendorIdFormat("1")).toBe(true);
    expect(isValidVendorIdFormat("123")).toBe(true);
    expect(isValidVendorIdFormat("9999")).toBe(true);
  });

  it("should return true for valid number ranges", () => {
    expect(isValidVendorIdFormat("1-10")).toBe(true);
    expect(isValidVendorIdFormat("15-300")).toBe(true);
    expect(isValidVendorIdFormat("100-999")).toBe(true);
  });

  it("should return false for invalid formats", () => {
    expect(isValidVendorIdFormat("")).toBe(false);
    expect(isValidVendorIdFormat("abc")).toBe(false);
    expect(isValidVendorIdFormat("1-")).toBe(false);
    expect(isValidVendorIdFormat("-10")).toBe(false);
    expect(isValidVendorIdFormat("1-1")).toBe(false); // Start must be less than end
    expect(isValidVendorIdFormat("10-5")).toBe(false); // Start must be less than end
    expect(isValidVendorIdFormat("a-10")).toBe(false);
    expect(isValidVendorIdFormat("10-b")).toBe(false);
    expect(isValidVendorIdFormat("1,2,3")).toBe(false);
  });
});

describe("parseVendorIdToRange", () => {
  it("should parse single numbers correctly", () => {
    expect(parseVendorIdToRange("1")).toEqual({ start: 1, end: 1 });
    expect(parseVendorIdToRange("123")).toEqual({ start: 123, end: 123 });
    expect(parseVendorIdToRange("9999")).toEqual({ start: 9999, end: 9999 });
  });

  it("should parse ranges correctly", () => {
    expect(parseVendorIdToRange("1-10")).toEqual({ start: 1, end: 10 });
    expect(parseVendorIdToRange("15-300")).toEqual({ start: 15, end: 300 });
    expect(parseVendorIdToRange("100-999")).toEqual({ start: 100, end: 999 });
  });

  it("should return null for invalid formats", () => {
    expect(parseVendorIdToRange("")).toBeNull();
    expect(parseVendorIdToRange("abc")).toBeNull();
    expect(parseVendorIdToRange("1-")).toBeNull();
    expect(parseVendorIdToRange("-10")).toBeNull();
    expect(parseVendorIdToRange("a-10")).toBeNull();
    expect(parseVendorIdToRange("10-b")).toBeNull();
    expect(parseVendorIdToRange("1,2,3")).toBeNull();
  });
});

describe("doRangesOverlap", () => {
  it("should detect overlapping ranges", () => {
    // Complete overlap
    expect(doRangesOverlap({ start: 1, end: 10 }, { start: 1, end: 10 })).toBe(
      true,
    );

    // Partial overlap
    expect(doRangesOverlap({ start: 1, end: 10 }, { start: 5, end: 15 })).toBe(
      true,
    );
    expect(doRangesOverlap({ start: 5, end: 15 }, { start: 1, end: 10 })).toBe(
      true,
    );

    // One range contains the other
    expect(doRangesOverlap({ start: 1, end: 20 }, { start: 5, end: 15 })).toBe(
      true,
    );
    expect(doRangesOverlap({ start: 5, end: 15 }, { start: 1, end: 20 })).toBe(
      true,
    );
  });

  it("should handle single value ranges correctly", () => {
    // Single value at the edge of a range
    expect(doRangesOverlap({ start: 1, end: 1 }, { start: 1, end: 10 })).toBe(
      true,
    );
    expect(doRangesOverlap({ start: 10, end: 10 }, { start: 1, end: 10 })).toBe(
      true,
    );

    // Single value inside a range
    expect(doRangesOverlap({ start: 5, end: 5 }, { start: 1, end: 10 })).toBe(
      true,
    );

    // Single value outside a range
    expect(doRangesOverlap({ start: 15, end: 15 }, { start: 1, end: 10 })).toBe(
      false,
    );

    // Two single values that match
    expect(doRangesOverlap({ start: 5, end: 5 }, { start: 5, end: 5 })).toBe(
      true,
    );

    // Two single values that don't match
    expect(doRangesOverlap({ start: 5, end: 5 }, { start: 6, end: 6 })).toBe(
      false,
    );
  });

  it("should handle null end values (unlimited ranges)", () => {
    // Range with null end should overlap with any range with start >= its start
    expect(
      doRangesOverlap({ start: 10, end: null }, { start: 5, end: 20 }),
    ).toBe(true);
    expect(
      doRangesOverlap({ start: 10, end: null }, { start: 10, end: 20 }),
    ).toBe(true);
    expect(
      doRangesOverlap({ start: 10, end: null }, { start: 15, end: 20 }),
    ).toBe(true);

    // Range with null end should not overlap with range that ends before its start
    expect(
      doRangesOverlap({ start: 10, end: null }, { start: 1, end: 5 }),
    ).toBe(false);

    // Two unlimited ranges should overlap if they have any overlap
    expect(
      doRangesOverlap({ start: 1, end: null }, { start: 10, end: null }),
    ).toBe(true);

    // Single value with unlimited range
    expect(doRangesOverlap({ start: 5, end: 5 }, { start: 1, end: null })).toBe(
      true,
    );
    expect(
      doRangesOverlap({ start: 5, end: 5 }, { start: 10, end: null }),
    ).toBe(false);
  });

  it("should detect non-overlapping ranges", () => {
    expect(doRangesOverlap({ start: 1, end: 5 }, { start: 6, end: 10 })).toBe(
      false,
    );
    expect(doRangesOverlap({ start: 6, end: 10 }, { start: 1, end: 5 })).toBe(
      false,
    );
  });
});

describe("checkForVendorRestrictionConflicts", () => {
  const purposeId = 1;
  const baseFormValues: FormValues = {
    restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
    vendor_restriction: TCFVendorRestriction.RESTRICT_SPECIFIC_VENDORS,
    vendor_ids: ["1-10"],
  };

  it("should return false when there are no existing restrictions", () => {
    const result = checkForVendorRestrictionConflicts(
      baseFormValues,
      [],
      purposeId,
    );
    expect(result).toBe(false);
  });

  it("should return false when there are no vendor IDs", () => {
    const result = checkForVendorRestrictionConflicts(
      { ...baseFormValues, vendor_ids: [] },
      [],
      purposeId,
    );
    expect(result).toBe(false);
  });

  it("should return false when existing restrictions are for a different purpose", () => {
    const existingRestrictions: PurposeRestriction[] = [
      {
        purpose_id: 2, // Different purpose ID
        restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
        vendor_restriction: TCFVendorRestriction.RESTRICT_SPECIFIC_VENDORS,
        vendor_ids: ["1-10"],
      },
    ];

    const result = checkForVendorRestrictionConflicts(
      baseFormValues,
      existingRestrictions,
      purposeId,
    );
    expect(result).toBe(false);
  });

  it("should return false when existing restrictions have a different restriction type", () => {
    const existingRestrictions: PurposeRestriction[] = [
      {
        purpose_id: purposeId,
        restriction_type: TCFRestrictionType.REQUIRE_CONSENT, // Different restriction type
        vendor_restriction: TCFVendorRestriction.RESTRICT_SPECIFIC_VENDORS,
        vendor_ids: ["1-10"],
      },
    ];

    const result = checkForVendorRestrictionConflicts(
      baseFormValues,
      existingRestrictions,
      purposeId,
    );
    expect(result).toBe(false);
  });

  it("should detect RESTRICT_ALL conflicts", () => {
    // When existing restriction is RESTRICT_ALL
    const existingRestrictions: PurposeRestriction[] = [
      {
        purpose_id: purposeId,
        restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
        vendor_restriction: TCFVendorRestriction.RESTRICT_ALL_VENDORS,
        vendor_ids: [],
      },
    ];

    const result = checkForVendorRestrictionConflicts(
      baseFormValues,
      existingRestrictions,
      purposeId,
    );
    expect(result).toBe(true);

    // When new restriction is RESTRICT_ALL and there are existing specific restrictions
    const formValuesWithRestrictAll: FormValues = {
      restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
      vendor_restriction: TCFVendorRestriction.RESTRICT_ALL_VENDORS,
      vendor_ids: [],
    };

    const existingSpecificRestrictions: PurposeRestriction[] = [
      {
        purpose_id: purposeId,
        restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
        vendor_restriction: TCFVendorRestriction.RESTRICT_SPECIFIC_VENDORS,
        vendor_ids: ["1-10"],
      },
    ];

    const result2 = checkForVendorRestrictionConflicts(
      formValuesWithRestrictAll,
      existingSpecificRestrictions,
      purposeId,
    );
    expect(result2).toBe(true);
  });

  it("should detect conflicts between RESTRICT_SPECIFIC and ALLOW_SPECIFIC", () => {
    const formValuesWithRestrictSpecific: FormValues = {
      restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
      vendor_restriction: TCFVendorRestriction.RESTRICT_SPECIFIC_VENDORS,
      vendor_ids: ["1-10"],
    };

    const existingAllowSpecificRestrictions: PurposeRestriction[] = [
      {
        purpose_id: purposeId,
        restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
        vendor_restriction: TCFVendorRestriction.ALLOW_SPECIFIC_VENDORS,
        vendor_ids: ["5-15"], // Overlaps with 1-10
      },
    ];

    const result = checkForVendorRestrictionConflicts(
      formValuesWithRestrictSpecific,
      existingAllowSpecificRestrictions,
      purposeId,
    );
    expect(result).toBe(true);

    // Test with non-overlapping ranges
    const existingNonOverlappingRestrictions: PurposeRestriction[] = [
      {
        purpose_id: purposeId,
        restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
        vendor_restriction: TCFVendorRestriction.ALLOW_SPECIFIC_VENDORS,
        vendor_ids: ["20-30"], // Does not overlap with 1-10
      },
    ];

    const result2 = checkForVendorRestrictionConflicts(
      formValuesWithRestrictSpecific,
      existingNonOverlappingRestrictions,
      purposeId,
    );
    expect(result2).toBe(false);
  });

  it("should detect duplicate ranges for the same restriction type", () => {
    const formValuesWithRestrictSpecific: FormValues = {
      restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
      vendor_restriction: TCFVendorRestriction.RESTRICT_SPECIFIC_VENDORS,
      vendor_ids: ["1-10"],
    };

    const existingRestrictSpecificRestrictions: PurposeRestriction[] = [
      {
        purpose_id: purposeId,
        restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
        vendor_restriction: TCFVendorRestriction.RESTRICT_SPECIFIC_VENDORS,
        vendor_ids: ["5-15"], // Overlaps with 1-10
      },
    ];

    const result = checkForVendorRestrictionConflicts(
      formValuesWithRestrictSpecific,
      existingRestrictSpecificRestrictions,
      purposeId,
    );
    expect(result).toBe(true);

    // Test with non-overlapping ranges
    const existingNonOverlappingRestrictions: PurposeRestriction[] = [
      {
        purpose_id: purposeId,
        restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
        vendor_restriction: TCFVendorRestriction.RESTRICT_SPECIFIC_VENDORS,
        vendor_ids: ["20-30"], // Does not overlap with 1-10
      },
    ];

    const result2 = checkForVendorRestrictionConflicts(
      formValuesWithRestrictSpecific,
      existingNonOverlappingRestrictions,
      purposeId,
    );
    expect(result2).toBe(false);
  });

  it("should handle invalid vendor IDs properly", () => {
    const formValuesWithInvalidIds: FormValues = {
      restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
      vendor_restriction: TCFVendorRestriction.RESTRICT_SPECIFIC_VENDORS,
      vendor_ids: ["invalid", "also-invalid"],
    };

    const existingRestrictions: PurposeRestriction[] = [
      {
        purpose_id: purposeId,
        restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
        vendor_restriction: TCFVendorRestriction.RESTRICT_SPECIFIC_VENDORS,
        vendor_ids: ["1-10"],
      },
    ];

    // Should not error and return false since all IDs are invalid
    const result = checkForVendorRestrictionConflicts(
      formValuesWithInvalidIds,
      existingRestrictions,
      purposeId,
    );
    expect(result).toBe(false);

    // Should still detect conflicts with valid IDs
    const formValuesWithMixedIds: FormValues = {
      restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
      vendor_restriction: TCFVendorRestriction.RESTRICT_SPECIFIC_VENDORS,
      vendor_ids: ["invalid", "5"], // 5 is valid and would conflict
    };

    const result2 = checkForVendorRestrictionConflicts(
      formValuesWithMixedIds,
      existingRestrictions,
      purposeId,
    );
    expect(result2).toBe(true);
  });
});
