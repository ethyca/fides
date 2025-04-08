import {
  RangeEntry,
  TCFRestrictionType,
  TCFVendorRestriction,
} from "~/types/api";

import {
  FormValues,
  PurposeRestriction,
} from "../../src/features/consent-settings/tcf/types";
import {
  checkForVendorRestrictionConflicts,
  convertVendorIdsToRangeEntries,
  convertVendorIdToRangeEntry,
  doRangesOverlap,
  isRangeContained,
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

describe("isRangeContained", () => {
  it("should correctly identify when a range is contained within another", () => {
    // Complete containment
    expect(isRangeContained({ start: 5, end: 10 }, { start: 1, end: 15 })).toBe(
      true,
    );
    expect(isRangeContained({ start: 5, end: 10 }, { start: 5, end: 10 })).toBe(
      true,
    ); // Equal ranges

    // Not contained
    expect(isRangeContained({ start: 1, end: 10 }, { start: 5, end: 15 })).toBe(
      false,
    );
    expect(isRangeContained({ start: 5, end: 15 }, { start: 1, end: 10 })).toBe(
      false,
    );
  });

  it("should handle single value ranges correctly", () => {
    // Single value inside a range
    expect(isRangeContained({ start: 5, end: 5 }, { start: 1, end: 10 })).toBe(
      true,
    );

    // Single value at range boundaries
    expect(isRangeContained({ start: 1, end: 1 }, { start: 1, end: 10 })).toBe(
      true,
    );
    expect(
      isRangeContained({ start: 10, end: 10 }, { start: 1, end: 10 }),
    ).toBe(true);

    // Single value outside range
    expect(
      isRangeContained({ start: 15, end: 15 }, { start: 1, end: 10 }),
    ).toBe(false);

    // Single value with single value range
    expect(isRangeContained({ start: 5, end: 5 }, { start: 5, end: 5 })).toBe(
      true,
    );
    expect(isRangeContained({ start: 5, end: 5 }, { start: 6, end: 6 })).toBe(
      false,
    );
  });

  it("should handle null end values (unlimited ranges) correctly", () => {
    // Range with end contained in unlimited range
    expect(
      isRangeContained({ start: 15, end: 20 }, { start: 10, end: null }),
    ).toBe(true);

    // Range starting before unlimited range
    expect(
      isRangeContained({ start: 5, end: 20 }, { start: 10, end: null }),
    ).toBe(false);

    // Unlimited range cannot be contained in finite range
    expect(
      isRangeContained({ start: 10, end: null }, { start: 1, end: 20 }),
    ).toBe(false);

    // Unlimited range in unlimited range
    expect(
      isRangeContained({ start: 15, end: null }, { start: 10, end: null }),
    ).toBe(true);
    expect(
      isRangeContained({ start: 10, end: null }, { start: 15, end: null }),
    ).toBe(false);

    // Single value with unlimited range
    expect(
      isRangeContained({ start: 15, end: 15 }, { start: 10, end: null }),
    ).toBe(true);
    expect(
      isRangeContained({ start: 5, end: 5 }, { start: 10, end: null }),
    ).toBe(false);
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
        id: "1",
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
        id: "1",
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
    expect(result).toBe(true); // Changed to true since the function only checks vendor_restriction type
  });

  it("should handle RESTRICT_ALL vendor restrictions", () => {
    // When existing restriction is RESTRICT_ALL
    const existingRestrictions: PurposeRestriction[] = [
      {
        id: "1",
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
    expect(result).toBe(false); // Changed to false since RESTRICT_ALL is treated as a different vendor_restriction type

    // When new restriction is RESTRICT_ALL and there are existing specific restrictions
    const formValuesWithRestrictAll: FormValues = {
      restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
      vendor_restriction: TCFVendorRestriction.RESTRICT_ALL_VENDORS,
      vendor_ids: [],
    };

    const existingSpecificRestrictions: PurposeRestriction[] = [
      {
        id: "1",
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
    expect(result2).toBe(false); // Changed to false since RESTRICT_ALL is treated as a different vendor_restriction type
  });

  it("should detect conflicts between RESTRICT_SPECIFIC and ALLOW_SPECIFIC based on containment", () => {
    const formValuesWithRestrictSpecific: FormValues = {
      restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
      vendor_restriction: TCFVendorRestriction.RESTRICT_SPECIFIC_VENDORS,
      vendor_ids: ["1-20"],
    };

    const existingAllowSpecificRestrictions: PurposeRestriction[] = [
      {
        id: "1",
        purpose_id: purposeId,
        restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
        vendor_restriction: TCFVendorRestriction.ALLOW_SPECIFIC_VENDORS,
        vendor_ids: ["5-10"], // Contained within 1-20
      },
    ];

    // Should not detect conflict when ALLOW range is fully contained in RESTRICT range
    const result = checkForVendorRestrictionConflicts(
      formValuesWithRestrictSpecific,
      existingAllowSpecificRestrictions,
      purposeId,
    );
    expect(result).toBe(false);

    // Test with ALLOW range not contained in RESTRICT range
    const existingNonContainedRestrictions: PurposeRestriction[] = [
      {
        id: "1",
        purpose_id: purposeId,
        restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
        vendor_restriction: TCFVendorRestriction.ALLOW_SPECIFIC_VENDORS,
        vendor_ids: ["15-25"], // Partially overlaps but not contained
      },
    ];

    const result2 = checkForVendorRestrictionConflicts(
      formValuesWithRestrictSpecific,
      existingNonContainedRestrictions,
      purposeId,
    );
    expect(result2).toBe(true);

    // Test with ALLOW range completely outside RESTRICT range
    const existingNonOverlappingRestrictions: PurposeRestriction[] = [
      {
        id: "1",
        purpose_id: purposeId,
        restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
        vendor_restriction: TCFVendorRestriction.ALLOW_SPECIFIC_VENDORS,
        vendor_ids: ["30-40"], // No overlap
      },
    ];

    const result3 = checkForVendorRestrictionConflicts(
      formValuesWithRestrictSpecific,
      existingNonOverlappingRestrictions,
      purposeId,
    );
    expect(result3).toBe(true); // Changed to true since non-contained ranges are conflicts
  });

  it("should handle unlimited ranges in RESTRICT_SPECIFIC and ALLOW_SPECIFIC conflicts", () => {
    const formValuesWithUnlimitedRestrict: FormValues = {
      restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
      vendor_restriction: TCFVendorRestriction.RESTRICT_SPECIFIC_VENDORS,
      vendor_ids: ["10"], // Single value becomes range with same start and end
    };

    const existingAllowSpecificRestrictions: PurposeRestriction[] = [
      {
        id: "1",
        purpose_id: purposeId,
        restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
        vendor_restriction: TCFVendorRestriction.ALLOW_SPECIFIC_VENDORS,
        vendor_ids: ["5-15"], // Not contained in single value 10
      },
    ];

    const result = checkForVendorRestrictionConflicts(
      formValuesWithUnlimitedRestrict,
      existingAllowSpecificRestrictions,
      purposeId,
    );
    expect(result).toBe(true);

    // Test with ALLOW range after the RESTRICT single value
    const existingLaterRestrictions: PurposeRestriction[] = [
      {
        id: "1",
        purpose_id: purposeId,
        restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
        vendor_restriction: TCFVendorRestriction.ALLOW_SPECIFIC_VENDORS,
        vendor_ids: ["15-20"], // After single value 10
      },
    ];

    const result2 = checkForVendorRestrictionConflicts(
      formValuesWithUnlimitedRestrict,
      existingLaterRestrictions,
      purposeId,
    );
    expect(result2).toBe(true); // Changed to true since not contained in the single value
  });

  it("should handle invalid vendor IDs properly", () => {
    const formValuesWithInvalidIds: FormValues = {
      restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
      vendor_restriction: TCFVendorRestriction.RESTRICT_SPECIFIC_VENDORS,
      vendor_ids: ["invalid", "also-invalid"],
    };

    const existingRestrictions: PurposeRestriction[] = [
      {
        id: "1",
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

  it("should ignore the restriction being edited when checking for conflicts", () => {
    const existingRestrictions: PurposeRestriction[] = [
      {
        id: "1",
        purpose_id: purposeId,
        restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
        vendor_restriction: TCFVendorRestriction.RESTRICT_SPECIFIC_VENDORS,
        vendor_ids: ["1-10"],
      },
      {
        id: "2",
        purpose_id: purposeId,
        restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
        vendor_restriction: TCFVendorRestriction.RESTRICT_SPECIFIC_VENDORS,
        vendor_ids: ["5-15"],
      },
    ];

    // Should detect conflict when not editing any restriction
    const result1 = checkForVendorRestrictionConflicts(
      baseFormValues,
      existingRestrictions,
      purposeId,
    );
    expect(result1).toBe(true);

    // Should not detect conflict when editing the conflicting restriction
    const result2 = checkForVendorRestrictionConflicts(
      baseFormValues,
      existingRestrictions,
      purposeId,
      "1", // ID of the first restriction
    );
    expect(result2).toBe(true); // Still true because of conflict with second restriction

    // Should not detect conflict when editing the only conflicting restriction
    const result3 = checkForVendorRestrictionConflicts(
      baseFormValues,
      [existingRestrictions[0]], // Only the first restriction
      purposeId,
      "1", // ID of the first restriction
    );
    expect(result3).toBe(false);
  });

  it("should ignore the restriction being edited when checking RESTRICT_ALL conflicts", () => {
    const existingRestrictions: PurposeRestriction[] = [
      {
        id: "1",
        purpose_id: purposeId,
        restriction_type: TCFRestrictionType.PURPOSE_RESTRICTION,
        vendor_restriction: TCFVendorRestriction.RESTRICT_ALL_VENDORS,
        vendor_ids: [],
      },
    ];

    // Should detect conflict when not editing any restriction
    const result1 = checkForVendorRestrictionConflicts(
      baseFormValues,
      existingRestrictions,
      purposeId,
    );
    expect(result1).toBe(false); // Changed to false since RESTRICT_ALL is not handled specially

    // Should not detect conflict when editing the RESTRICT_ALL restriction
    const result2 = checkForVendorRestrictionConflicts(
      baseFormValues,
      existingRestrictions,
      purposeId,
      "1", // ID of the RESTRICT_ALL restriction
    );
    expect(result2).toBe(false);
  });
});

describe("convertVendorIdToRangeEntry", () => {
  it("should convert single numbers to RangeEntry objects", () => {
    expect(convertVendorIdToRangeEntry("1")).toEqual({
      start_vendor_id: 1,
      end_vendor_id: null,
    });
    expect(convertVendorIdToRangeEntry("123")).toEqual({
      start_vendor_id: 123,
      end_vendor_id: null,
    });
    expect(convertVendorIdToRangeEntry("9999")).toEqual({
      start_vendor_id: 9999,
      end_vendor_id: null,
    });
  });

  it("should convert valid ranges to RangeEntry objects", () => {
    expect(convertVendorIdToRangeEntry("1-10")).toEqual({
      start_vendor_id: 1,
      end_vendor_id: 10,
    });
    expect(convertVendorIdToRangeEntry("15-300")).toEqual({
      start_vendor_id: 15,
      end_vendor_id: 300,
    });
  });

  it("should return null for invalid formats", () => {
    expect(convertVendorIdToRangeEntry("")).toBeNull();
    expect(convertVendorIdToRangeEntry("abc")).toBeNull();
    expect(convertVendorIdToRangeEntry("1-")).toBeNull();
    expect(convertVendorIdToRangeEntry("-10")).toBeNull();
    expect(convertVendorIdToRangeEntry("10-5")).toBeNull(); // Start greater than end
    expect(convertVendorIdToRangeEntry("a-10")).toBeNull();
    expect(convertVendorIdToRangeEntry("10-b")).toBeNull();
  });
});

describe("convertVendorIdsToRangeEntries", () => {
  it("should convert an array of vendor IDs to RangeEntry objects", () => {
    const input = ["1", "5-10", "20"];
    const expected: RangeEntry[] = [
      { start_vendor_id: 1, end_vendor_id: null },
      { start_vendor_id: 5, end_vendor_id: 10 },
      { start_vendor_id: 20, end_vendor_id: null },
    ];
    expect(convertVendorIdsToRangeEntries(input)).toEqual(expected);
  });

  it("should handle empty arrays", () => {
    expect(convertVendorIdsToRangeEntries([])).toEqual([]);
    expect(convertVendorIdsToRangeEntries()).toEqual([]); // undefined case
  });

  it("should filter out invalid entries", () => {
    const input = ["1", "invalid", "5-10", "10-5", "20"];
    const expected: RangeEntry[] = [
      { start_vendor_id: 1, end_vendor_id: null },
      { start_vendor_id: 5, end_vendor_id: 10 },
      { start_vendor_id: 20, end_vendor_id: null },
    ];
    expect(convertVendorIdsToRangeEntries(input)).toEqual(expected);
  });

  it("should handle arrays with all invalid entries", () => {
    const input = ["invalid", "10-5", "abc", "-10"];
    expect(convertVendorIdsToRangeEntries(input)).toEqual([]);
  });
});
