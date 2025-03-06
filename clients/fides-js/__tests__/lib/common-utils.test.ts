import {
  getConsentValueFromOverride,
  isGlobalConsentOverride,
  isNoticeOverrides,
  isOverrideDisabled,
  isValidNoticeOverrideValue,
} from "~/lib/common-utils";
import { NoticeOverrideValue } from "~/lib/consent-types";

describe("Consent Override Utilities", () => {
  describe("isGlobalConsentOverride", () => {
    it("should return true for 'accept'", () => {
      expect(isGlobalConsentOverride("accept")).toBe(true);
    });
    it("should return true for 'reject'", () => {
      expect(isGlobalConsentOverride("reject")).toBe(true);
    });
    it("should return false for other values", () => {
      expect(isGlobalConsentOverride("other")).toBe(false);
      expect(isGlobalConsentOverride(1)).toBe(false);
      expect(isGlobalConsentOverride(null)).toBe(false);
      expect(isGlobalConsentOverride(undefined)).toBe(false);
    });
  });

  describe("isValidNoticeOverrideValue", () => {
    it("should return true for valid numeric values (1-4)", () => {
      expect(isValidNoticeOverrideValue(1)).toBe(true);
      expect(isValidNoticeOverrideValue(2)).toBe(true);
      expect(isValidNoticeOverrideValue(3)).toBe(true);
      expect(isValidNoticeOverrideValue(4)).toBe(true);
    });
    it("should return false for invalid values", () => {
      expect(isValidNoticeOverrideValue(0)).toBe(false);
      expect(isValidNoticeOverrideValue(5)).toBe(false);
      expect(isValidNoticeOverrideValue("1")).toBe(false);
      expect(isValidNoticeOverrideValue(null)).toBe(false);
    });
  });

  describe("isNoticeOverrides", () => {
    it("should return true for valid notice overrides object", () => {
      expect(isNoticeOverrides({ data_sales: 1, analytics: 2 })).toBe(true);
      expect(isNoticeOverrides({ notice1: 3, notice2: 4 })).toBe(true);
    });
    it("should return false for invalid objects", () => {
      expect(isNoticeOverrides({ data_sales: 5 })).toBe(false);
      expect(isNoticeOverrides({ data_sales: "1" })).toBe(false);
      expect(isNoticeOverrides(null)).toBe(false);
      expect(isNoticeOverrides(undefined)).toBe(false);
    });
  });

  describe("getConsentValueFromOverride", () => {
    it("should return true for accept values", () => {
      expect(getConsentValueFromOverride(NoticeOverrideValue.ACCEPT)).toBe(
        true,
      );
      expect(
        getConsentValueFromOverride(NoticeOverrideValue.ACCEPT_DISABLED),
      ).toBe(true);
    });
    it("should return false for reject values", () => {
      expect(getConsentValueFromOverride(NoticeOverrideValue.REJECT)).toBe(
        false,
      );
      expect(
        getConsentValueFromOverride(NoticeOverrideValue.REJECT_DISABLED),
      ).toBe(false);
    });
  });

  describe("isOverrideDisabled", () => {
    it("should return true for disabled values", () => {
      expect(isOverrideDisabled(NoticeOverrideValue.ACCEPT_DISABLED)).toBe(
        true,
      );
      expect(isOverrideDisabled(NoticeOverrideValue.REJECT_DISABLED)).toBe(
        true,
      );
    });
    it("should return false for non-disabled values", () => {
      expect(isOverrideDisabled(NoticeOverrideValue.ACCEPT)).toBe(false);
      expect(isOverrideDisabled(NoticeOverrideValue.REJECT)).toBe(false);
    });
  });
});
