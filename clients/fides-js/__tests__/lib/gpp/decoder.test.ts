import {
  decodeGppString,
  getGppField,
  hasGppSection,
} from "../../../src/lib/gpp/decoder";
import mockDecodedTCFJSON from "../../__fixtures__/mock_decoded_tcf.json";

describe("GPP Decoder", () => {
  describe("decodeGppString", () => {
    it("should decode a US National GPP string", () => {
      const gppString = "DBABLA~BVAoAAAAAABk.QA";
      const decoded = decodeGppString(gppString);
      expect(decoded).toHaveLength(1);
      const section = decoded[0];
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

    it("should decode a tcfeuv2 GPP string", () => {
      const gppString =
        "DBABMA~CQNb38AQNb38AGXABBENBeFgALAAAENAAAAAFyQAQFyAXJABAXIAAAAA";
      const decoded = decodeGppString(gppString);
      const mockDecodedTCF = mockDecodedTCFJSON as any;
      // format the date strings as Date objects
      mockDecodedTCF[0].data.Created = new Date(mockDecodedTCF[0].data.Created);
      mockDecodedTCF[0].data.LastUpdated = new Date(
        mockDecodedTCF[0].data.LastUpdated,
      );
      expect(decoded).toEqual(mockDecodedTCF);
    });

    it("should decode a US State (California) GPP string", () => {
      const gppString = "DBABBg~BUoAAABg.Q";
      const decoded = decodeGppString(gppString);
      expect(decoded).toHaveLength(1);
      const section = decoded[0];
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

    it("should decode a GPP string with multiple sections", () => {
      // This string contains both US National and US California sections
      const gppString = "DBABrw~BVAUAAAAAABk.QA~BAAAAABA.QA";
      const decoded = decodeGppString(gppString);
      expect(decoded).toHaveLength(2);

      // Check first section (US National)
      const usnatSection = decoded[0] as any;
      expect(usnatSection.id).toBe(7);
      expect(usnatSection.name).toBe("usnat");
      expect(usnatSection.data.Version).toBe(1);
      expect(usnatSection.data.SharingNotice).toBe(1);
      expect(usnatSection.data.SaleOptOut).toBe(1);
      expect(usnatSection.data.SharingOptOut).toBe(1);

      // Check second section (US California)
      const uscaSection = decoded[1] as any;
      expect(uscaSection.id).toBe(8);
      expect(uscaSection.name).toBe("usca");
      expect(uscaSection.data.Version).toBe(1);
      expect(uscaSection.data.SaleOptOut).toBe(0);
      expect(uscaSection.data.SharingOptOut).toBe(0);
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
