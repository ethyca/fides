import {
  decodeGppString,
  getGppField,
  hasGppSection,
} from "../../../src/lib/gpp/decoder";

describe("GPP Decoder", () => {
  describe("decodeGppString", () => {
    it("should decode a US National GPP string", () => {
      const gppString = "DBABLA~BVAoAAAAAABk.QA";
      const decoded = decodeGppString(gppString);

      expect(decoded.header.sectionIds).toEqual([7]); // US National section ID
      expect(decoded.sections).toHaveLength(1);

      const section = decoded.sections[0];
      expect(section).toEqual({
        id: 7,
        name: "usnat",
        data: {
          Version: 1,
          SharingNotice: 1,
          SaleOptOutNotice: 1,
          SharingOptOutNotice: 1,
          TargetedAdvertisingOptOutNotice: 0,
          SensitiveDataProcessingOptOutNotice: 0,
          KnownChildSensitiveDataConsents: [0, 0, 0],
          PersonalDataConsents: 0,
          MspaCoveredTransaction: 1,
          MspaOptOutOptionMode: 2,
          MspaServiceProviderMode: 1,
          SaleOptOut: 2,
          SharingOptOut: 2,
          TargetedAdvertisingOptOut: 0,
          SensitiveDataProcessing: Array(16).fill(0),
          Gpc: false,
          GpcSegmentType: 1,
          SensitiveDataLimitUseNotice: 0,
        },
      });
    });

    it("should decode a TCF EU v2 GPP string", () => {
      const gppString =
        "DBABMA~CQNb38AQNb38AGXABBENBeFgALAAAENAAAAAFyQAQFyAXJABAXIAAAAA";
      const decoded = decodeGppString(gppString);

      expect(decoded.header.sectionIds).toEqual([2]); // TCF EU v2 section ID
      expect(decoded.sections).toHaveLength(1);

      const section = decoded.sections[0];
      expect(section.id).toBe(2);
      expect(section.name).toBe("section_2"); // TCF EU v2 section is not mapped in FIDES_REGION_TO_GPP_SECTION
      expect(section.data).toBeDefined();
    });

    it("should decode a US State (California) GPP string", () => {
      const gppString = "DBABBg~BUoAAABg.Q";
      const decoded = decodeGppString(gppString);

      expect(decoded.header.sectionIds).toEqual([8]); // US State section ID
      expect(decoded.sections).toHaveLength(1);

      const section = decoded.sections[0];
      expect(section).toEqual({
        id: 8,
        name: "usca",
        data: {
          Version: 1,
          SaleOptOut: 2,
          SharingOptOut: 2,
          SensitiveDataProcessing: Array(9).fill(0),
          KnownChildSensitiveDataConsents: [0, 0],
          PersonalDataConsents: 0,
          MspaCoveredTransaction: 1,
          MspaOptOutOptionMode: 2,
          MspaServiceProviderMode: 0,
          SaleOptOutNotice: 1,
          SharingOptOutNotice: 1,
          SensitiveDataLimitUseNotice: 0,
          Gpc: false,
          GpcSegmentType: 1,
        },
      });
    });

    it("should handle invalid GPP strings", () => {
      expect(() => decodeGppString("invalid")).toThrow();
      expect(() => decodeGppString("")).toThrow("GPP string cannot be empty");
      expect(() => decodeGppString("DBAA")).not.toThrow(); // Empty but valid GPP string
    });
  });

  describe("getGppField", () => {
    it("should get a field value from US National section", () => {
      const gppString = "DBABLA~BVAoAAAAAABk.QA";

      expect(getGppField(gppString, "usnat", "Version")).toBe(1);
      expect(getGppField(gppString, "usnat", "SharingNotice")).toBe(1);
      expect(getGppField(gppString, "usnat", "NonexistentField")).toBeNull();
    });

    it("should handle invalid section names", () => {
      const gppString = "DBABLA~BVAoAAAAAABk.QA";
      expect(getGppField(gppString, "nonexistent", "Version")).toBeNull();
    });

    it("should handle invalid GPP strings", () => {
      expect(getGppField("invalid", "usnat", "Version")).toBeNull();
      expect(getGppField("", "usnat", "Version")).toBeNull();
    });
  });

  describe("hasGppSection", () => {
    it("should check for section existence", () => {
      const gppString = "DBABBg~BUoAAABg.Q";

      expect(hasGppSection(gppString, "usca")).toBe(true);
      expect(hasGppSection(gppString, "nonexistent")).toBe(false);
    });

    it("should handle invalid GPP strings", () => {
      expect(hasGppSection("invalid", "usnat")).toBe(false);
      expect(hasGppSection("", "usnat")).toBe(false);
    });
  });
});
