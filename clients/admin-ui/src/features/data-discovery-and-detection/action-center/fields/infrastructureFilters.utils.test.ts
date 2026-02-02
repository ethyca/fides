import { describe, expect, it } from "@jest/globals";

import { DiffStatus } from "~/types/api/models/DiffStatus";

import {
  InfrastructureStatusFilterOptionValue,
  parseFiltersToFilterValue,
} from "./utils";

describe("infrastructureFilters utils", () => {
  describe("parseFiltersToFilterValue", () => {
    it("returns KNOWN when vendor filter includes 'known'", () => {
      const result = parseFiltersToFilterValue(
        [DiffStatus.ADDITION],
        ["known"],
      );
      expect(result).toBe(InfrastructureStatusFilterOptionValue.KNOWN);
    });

    it("returns UNKNOWN when vendor filter includes 'unknown'", () => {
      const result = parseFiltersToFilterValue(
        [DiffStatus.ADDITION],
        ["unknown"],
      );
      expect(result).toBe(InfrastructureStatusFilterOptionValue.UNKNOWN);
    });

    it("returns NEW when status includes ADDITION and no vendor filter", () => {
      const result = parseFiltersToFilterValue([DiffStatus.ADDITION], []);
      expect(result).toBe(InfrastructureStatusFilterOptionValue.NEW);
    });

    it("returns IGNORED when status includes MUTED", () => {
      const result = parseFiltersToFilterValue([DiffStatus.MUTED], []);
      expect(result).toBe(InfrastructureStatusFilterOptionValue.IGNORED);
    });

    it("returns KNOWN even when status includes status filter", () => {
      const result = parseFiltersToFilterValue([DiffStatus.MUTED], ["known"]);
      expect(result).toBe(InfrastructureStatusFilterOptionValue.KNOWN);
    });

    it("returns undefined when filters don't match any option", () => {
      const result = parseFiltersToFilterValue(
        [DiffStatus.CLASSIFICATION_ADDITION],
        ["something_invalid"],
      );
      expect(result).toBeUndefined();
    });

    it("return undefined when status filters are empty and vendor filters are empty", () => {
      const result = parseFiltersToFilterValue([], []);
      expect(result).toBeUndefined();
    });

    it("handles multiple status filters correctly", () => {
      // Should match if ADDITION is included
      const result = parseFiltersToFilterValue(
        [DiffStatus.ADDITION, DiffStatus.MUTED],
        [],
      );
      // Should return NEW because ADDITION is present and no vendor filter
      expect(result).toBe(InfrastructureStatusFilterOptionValue.NEW);
    });

    it("handles multiple vendor filters correctly", () => {
      // Should match if "known" is included
      const result = parseFiltersToFilterValue(
        [DiffStatus.ADDITION],
        ["known", "unknown"],
      );
      // Should return KNOWN because "known" is checked first
      expect(result).toBe(InfrastructureStatusFilterOptionValue.KNOWN);
    });
  });
});
