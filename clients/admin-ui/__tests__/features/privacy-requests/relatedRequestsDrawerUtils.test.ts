import {
  extractIdentityFields,
  formatLabelList,
} from "~/features/privacy-requests/events-and-logs/relatedRequestsDrawerUtils";
import { PrivacyRequestEntity } from "~/features/privacy-requests/types";

type Identity = PrivacyRequestEntity["identity"];

describe("relatedRequestsDrawerUtils", () => {
  describe(extractIdentityFields.name, () => {
    it("returns undefined when identity is undefined", () => {
      expect(extractIdentityFields(undefined)).toBeUndefined();
    });

    it("returns undefined when every field is null or empty", () => {
      const identity: Identity = {
        email: { label: "Email", value: null },
        phone_number: { label: "Phone number", value: "" },
      };
      expect(extractIdentityFields(identity)).toBeUndefined();
    });

    it("extracts a single email identity", () => {
      const identity: Identity = {
        email: { label: "Email", value: "user@example.com" },
        phone_number: { label: "Phone number", value: null },
      };
      expect(extractIdentityFields(identity)).toEqual({
        filter: { email: "user@example.com" },
        labels: ["Email"],
      });
    });

    it("extracts a single phone identity", () => {
      const identity: Identity = {
        email: { label: "Email", value: null },
        phone_number: { label: "Phone number", value: "+15551234567" },
      };
      expect(extractIdentityFields(identity)).toEqual({
        filter: { phone_number: "+15551234567" },
        labels: ["Phone number"],
      });
    });

    it("extracts a single external id identity", () => {
      const identity: Identity = {
        external_id: { label: "External id", value: "ext-42" },
      };
      expect(extractIdentityFields(identity)).toEqual({
        filter: { external_id: "ext-42" },
        labels: ["External id"],
      });
    });

    it("extracts a single custom id identity", () => {
      const identity: Identity = {
        loyalty_id: { label: "Loyalty ID", value: "CH-1" },
      };
      expect(extractIdentityFields(identity)).toEqual({
        filter: { loyalty_id: "CH-1" },
        labels: ["Loyalty ID"],
      });
    });

    it("extracts two identities (email + phone)", () => {
      const identity: Identity = {
        email: { label: "Email", value: "user@example.com" },
        phone_number: { label: "Phone number", value: "+15551234567" },
      };
      expect(extractIdentityFields(identity)).toEqual({
        filter: {
          email: "user@example.com",
          phone_number: "+15551234567",
        },
        labels: ["Email", "Phone number"],
      });
    });

    it("extracts three identities (email + phone + custom)", () => {
      const identity: Identity = {
        email: { label: "Email", value: "user@example.com" },
        phone_number: { label: "Phone number", value: "+15551234567" },
        loyalty_id: { label: "Loyalty ID", value: "CH-1" },
      };
      expect(extractIdentityFields(identity)).toEqual({
        filter: {
          email: "user@example.com",
          phone_number: "+15551234567",
          loyalty_id: "CH-1",
        },
        labels: ["Email", "Phone number", "Loyalty ID"],
      });
    });

    it("skips fields with null/empty values when others are present", () => {
      const identity: Identity = {
        email: { label: "Email", value: "user@example.com" },
        phone_number: { label: "Phone number", value: null },
        external_id: { label: "External id", value: "" },
        loyalty_id: { label: "Loyalty ID", value: "CH-1" },
      };
      expect(extractIdentityFields(identity)).toEqual({
        filter: {
          email: "user@example.com",
          loyalty_id: "CH-1",
        },
        labels: ["Email", "Loyalty ID"],
      });
    });

    it("preserves the iteration order of the source identity object", () => {
      const identity: Identity = {
        loyalty_id: { label: "Loyalty ID", value: "CH-1" },
        email: { label: "Email", value: "user@example.com" },
      };
      const result = extractIdentityFields(identity);
      expect(result?.labels).toEqual(["Loyalty ID", "Email"]);
      expect(Object.keys(result?.filter ?? {})).toEqual([
        "loyalty_id",
        "email",
      ]);
    });
  });

  describe(formatLabelList.name, () => {
    it("returns an empty string for no labels", () => {
      expect(formatLabelList([])).toBe("");
    });

    it("returns a single label unchanged", () => {
      expect(formatLabelList(["Email"])).toBe("Email");
    });

    it("joins two labels with 'or'", () => {
      expect(formatLabelList(["Email", "Phone number"])).toBe(
        "Email or Phone number",
      );
    });

    it("joins three labels with commas and an Oxford 'or'", () => {
      expect(formatLabelList(["Email", "Phone number", "Loyalty ID"])).toBe(
        "Email, Phone number, or Loyalty ID",
      );
    });

    it("joins four labels with commas and an Oxford 'or'", () => {
      expect(
        formatLabelList(["Email", "Phone number", "External id", "Loyalty ID"]),
      ).toBe("Email, Phone number, External id, or Loyalty ID");
    });
  });
});
