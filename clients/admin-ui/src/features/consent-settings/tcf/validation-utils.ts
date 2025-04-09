import { RangeEntry, TCFVendorRestriction } from "~/types/api";

import { FormValues, PurposeRestriction } from "./types";

interface VendorRange {
  start: number;
  end: number | null;
}

export const ERROR_MESSAGE =
  "One or more of these vendors already have a restriction for this purpose. Please update the existing restriction or remove duplicates.";

// Validates a single vendor ID or range (e.g., "10" or "15-300")
export const isValidVendorIdFormat = (value: string): boolean => {
  // Check if it's a single number
  if (/^\d+$/.test(value)) {
    return true;
  }

  // Check if it's a range (e.g., "15-300")
  const rangeMatch = value.match(/^(\d+)-(\d+)$/);
  if (rangeMatch) {
    const start = parseInt(rangeMatch[1], 10);
    const end = parseInt(rangeMatch[2], 10);
    return start < end; // Start must be less than end
  }

  return false;
};

// Parse a vendor ID string to a range object
export const parseVendorIdToRange = (vendorId: string): VendorRange | null => {
  // Check if it's a single number
  if (/^\d+$/.test(vendorId)) {
    const num = parseInt(vendorId, 10);
    return { start: num, end: num };
  }

  // Parse range (e.g., "15-300")
  const rangeMatch = vendorId.match(/^(\d+)-(\d+)$/);
  if (rangeMatch) {
    return {
      start: parseInt(rangeMatch[1], 10),
      end: parseInt(rangeMatch[2], 10),
    };
  }

  // Return null for invalid formats instead of throwing an error
  return null;
};

/**
 * Checks if two vendor ranges share any values in common
 * @example
 * doRangesOverlap({start: 1, end: 10}, {start: 5, end: 15}) // true - shares 5-10
 * doRangesOverlap({start: 1, end: 5}, {start: 6, end: 10}) // false - no overlap
 */
export const doRangesOverlap = (
  range1: VendorRange,
  range2: VendorRange,
): boolean => {
  // If either range is a single value, check if it falls within the other range
  if (range1.end === range1.start) {
    return (
      range1.start >= range2.start &&
      (range2.end === null || range1.start <= range2.end)
    );
  }

  if (range2.end === range2.start) {
    return (
      range2.start >= range1.start &&
      (range1.end === null || range2.start <= range1.end)
    );
  }

  // Handle case where one range has a null end (unlimited upper bound)
  if (range1.end === null && range2.end !== null) {
    // Range with null end only overlaps if its start is <= the other range's end
    return range1.start <= range2.end;
  }

  if (range2.end === null && range1.end !== null) {
    // Range with null end only overlaps if its start is <= the other range's end
    return range2.start <= range1.end;
  }

  if (range1.end === null && range2.end === null) {
    // Two unlimited ranges overlap if either start is >= the other start
    return true;
  }

  // Both ranges have defined end points, check for overlap
  return (
    (range1.start <= range2.end! && range1.end! >= range2.start) ||
    (range2.start <= range1.end! && range2.end! >= range1.start)
  );
};

/**
 * Checks if range1 is fully contained within range2
 * @example
 * isRangeContained({start: 5, end: 10}, {start: 1, end: 15}) // true - 5-10 inside 1-15
 * isRangeContained({start: 1, end: 10}, {start: 5, end: 15}) // false - 1-4 outside
 */
export const isRangeContained = (
  range1: VendorRange,
  range2: VendorRange,
): boolean => {
  // If range1 is a single value
  if (range1.end === range1.start) {
    return (
      range1.start >= range2.start &&
      (range2.end === null || range1.start <= range2.end)
    );
  }

  // If range2 has no upper bound (null end), range1 must start after range2.start
  if (range2.end === null) {
    return range1.start >= range2.start;
  }

  // If range1 has no upper bound, it can't be contained in range2 (which has an upper bound)
  if (range1.end === null) {
    return false;
  }

  // Check if range1 is fully contained within range2
  return range1.start >= range2.start && range1.end <= range2.end;
};

// Check for conflicts between RESTRICT_SPECIFIC and ALLOW_SPECIFIC
export const checkForVendorRestrictionConflicts = (
  values: FormValues,
  existingRestrictions: PurposeRestriction[],
  purposeId?: number,
  restrictionBeingEditedId?: string,
): boolean => {
  // Filter to only get restrictions for the current purpose, excluding the one being edited
  const relevantRestrictions = existingRestrictions.filter(
    (r) => r.purpose_id === purposeId && r.id !== restrictionBeingEditedId,
  );

  // Return false if there are no vendor IDs to check
  if (!values.vendor_ids?.length) {
    return false;
  }

  // Convert current vendor_ids to ranges and filter out invalid formats
  const currentRanges = values.vendor_ids
    .map(parseVendorIdToRange)
    .filter((range): range is VendorRange => range !== null);

  // Return early if there are no valid ranges
  if (currentRanges.length === 0) {
    return false;
  }

  // Check for conflicts with existing restrictions
  return relevantRestrictions.some((restriction) => {
    // Check for opposite vendor restriction types (RESTRICT_SPECIFIC vs ALLOW_SPECIFIC)
    const isOppositeRestrictionType =
      (values.vendor_restriction ===
        TCFVendorRestriction.RESTRICT_SPECIFIC_VENDORS &&
        restriction.vendor_restriction ===
          TCFVendorRestriction.ALLOW_SPECIFIC_VENDORS) ||
      (values.vendor_restriction ===
        TCFVendorRestriction.ALLOW_SPECIFIC_VENDORS &&
        restriction.vendor_restriction ===
          TCFVendorRestriction.RESTRICT_SPECIFIC_VENDORS);

    // Convert restriction's vendor_ids to ranges and filter out invalid formats
    const existingRanges = restriction.vendor_ids
      .map(parseVendorIdToRange)
      .filter((range): range is VendorRange => range !== null);

    // Check for conflicts when restriction types are opposite
    if (isOppositeRestrictionType) {
      if (
        values.vendor_restriction ===
        TCFVendorRestriction.ALLOW_SPECIFIC_VENDORS
      ) {
        // For ALLOW_SPECIFIC: ALL existing RESTRICT ranges must be contained within ALL new ALLOW ranges
        return existingRanges.some((restrictRange) =>
          currentRanges.some(
            (allowRange) => !isRangeContained(restrictRange, allowRange),
          ),
        );
      }
      // For RESTRICT_SPECIFIC: ALL new RESTRICT ranges must be contained within ALL existing ALLOW ranges
      return currentRanges.some((restrictRange) =>
        existingRanges.some(
          (allowRange) => !isRangeContained(restrictRange, allowRange),
        ),
      );
    }

    // Check for duplicates when restriction types are the same
    if (restriction.vendor_restriction === values.vendor_restriction) {
      // Check if any ranges overlap
      return currentRanges.some((currentRange) =>
        existingRanges.some((existingRange) =>
          doRangesOverlap(currentRange, existingRange),
        ),
      );
    }

    return false;
  });
};

/**
 * Converts a vendor ID string to a RangeEntry object
 * @param vendorId A string representing either a single vendor ID (e.g. "10") or a range (e.g. "15-300")
 * @returns A RangeEntry object or null if the format is invalid
 */
export const convertVendorIdToRangeEntry = (
  vendorId: string,
): RangeEntry | null => {
  // Check if it's a single number
  if (/^\d+$/.test(vendorId)) {
    const num = parseInt(vendorId, 10);
    return { start_vendor_id: num, end_vendor_id: null };
  }

  // Parse range (e.g., "15-300")
  const rangeMatch = vendorId.match(/^(\d+)-(\d+)$/);
  if (rangeMatch) {
    const start = parseInt(rangeMatch[1], 10);
    const end = parseInt(rangeMatch[2], 10);
    if (start < end) {
      return {
        start_vendor_id: start,
        end_vendor_id: end,
      };
    }
  }

  return null;
};

/**
 * Converts an array of vendor ID strings to RangeEntry objects
 * @param vendorIds Array of vendor ID strings
 * @returns Array of valid RangeEntry objects
 */
export const convertVendorIdsToRangeEntries = (
  vendorIds: string[] = [],
): RangeEntry[] => {
  return vendorIds
    .map(convertVendorIdToRangeEntry)
    .filter((entry): entry is RangeEntry => entry !== null);
};
